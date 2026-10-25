"""Run from backend: python -m app.pipeline.train"""
import argparse
import hashlib
import json
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
TARGET = 'target_overtake_3lap'
CATEGORICAL = ['attacker_compound', 'defender_compound']
NUMERIC = [
    'gap', 'attacker_position', 'defender_position',
    'attacker_lap', 'defender_lap', 'seconds_since_lap_start',
    'attacker_tyre_age', 'defender_tyre_age', 'tyre_age_diff',
    'attacker_recent_pace', 'defender_recent_pace', 'recent_race_pace_diff',
    'attacker_pace_lap_count', 'defender_pace_lap_count',
    'battle_age_seconds', 'time_within_1_sec',
    'gap_mean_last_lap', 'gap_trend_last_lap', 'gap_1_lap_ago',
    'gap_history_complete', 'gap_history_window_seconds',
    'defender_gap_ahead', 'defender_in_train', 'defender_is_leader',
]
FEATURES = NUMERIC + CATEGORICAL
IDENTITY = ['session_key', 'prediction_time', 'attacker_number', 'defender_number']


def feature_frame(frame):
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing features: {sorted(missing)}')
    out = frame[FEATURES].copy()
    for name in NUMERIC:
        out[name] = pd.to_numeric(out[name], errors='raise').astype('float64')
    if np.isinf(out[NUMERIC].to_numpy()).any():
        raise ValueError('Infinite numeric feature')
    for name in CATEGORICAL:
        out[name] = out[name].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return out


def load_dataset(processed_root, sessions):
    if len(sessions) < 3 or len(set(sessions)) != len(sessions):
        raise ValueError('Provide at least three distinct session keys')
    frames, sources = [], []
    required = set(FEATURES + IDENTITY + [TARGET, 'battle_id', 'battle_ready',
                                        'offline_eligible', 'label_version'])
    for key in sessions:
        path = processed_root / str(key) / 'labeled_3lap_v2.parquet'
        frame = pd.read_parquet(path)
        if required - set(frame.columns):
            raise ValueError(f'{path}: missing columns {sorted(required - set(frame.columns))}')
        if frame.empty or not frame.session_key.eq(key).all():
            raise ValueError(f'{path}: empty file or mismatched session_key')
        known = frame[TARGET].notna()
        if not frame.loc[known, TARGET].isin([0, 1]).all():
            raise ValueError(f'{path}: target must be 0, 1 or NA')
        selected = frame.loc[known].copy()
        if selected.empty:
            raise ValueError(f'{path}: no known labels')
        if not (selected.battle_ready.eq(True) & selected.offline_eligible.eq(True)).fillna(False).all():
            raise ValueError(f'{path}: labeled rows fail eligibility checks')
        if selected[IDENTITY + ['battle_id', 'label_version']].isna().any().any():
            raise ValueError(f'{path}: missing identity or label version')
        selected['prediction_time'] = pd.to_datetime(selected.prediction_time, utc=True, errors='raise')
        selected[TARGET] = selected[TARGET].astype(int)
        frames.append(selected)
        sources.append({'session_key': key, 'path': str(path.resolve()),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'total_rows': len(frame), 'known_rows': len(selected),
                        'positive_rows': int(selected[TARGET].sum())})
    data = pd.concat(frames, ignore_index=True).sort_values(IDENTITY).reset_index(drop=True)
    if data.duplicated(['session_key', 'attacker_number', 'prediction_time']).any():
        raise ValueError('Duplicate attacker observations')
    if set(data.label_version) != {'v2-gap-evidence'}:
        raise ValueError('Expected label_version v2-gap-evidence')
    feature_frame(data)
    data['row_id'] = np.arange(len(data))
    return data, sources


def race_splits(data):
    groups = data.session_key.to_numpy()
    for key in sorted(data.session_key.unique()):
        yield int(key), np.flatnonzero(groups != key), np.flatnonzero(groups == key)


def forward_splits(data, min_train_races=3):
    bounds = data.groupby('session_key').prediction_time.agg(['min', 'max']).sort_values('min')
    if not 2 <= min_train_races < len(bounds):
        raise ValueError('Need at least min_train_races + 1 races, with min_train_races >= 2')
    keys = list(bounds.index)
    for i in range(1, len(keys)):
        if bounds.loc[keys[:i], 'max'].max() >= bounds.loc[keys[i], 'min']:
            raise ValueError('Race observation times overlap')
    for i in range(min_train_races, len(keys)):
        yield int(keys[i]), np.flatnonzero(data.session_key.isin(keys[:i])), np.flatnonzero(data.session_key.eq(keys[i]))


def make_model(name, seed=42, jobs=2):
    categories = Pipeline([
        ('impute', SimpleImputer(strategy='constant', fill_value='UNKNOWN', keep_empty_features=True)),
        ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])
    if name == 'logistic':
        numeric = Pipeline([
            ('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
            ('scale', StandardScaler()),
        ])
        estimator = LogisticRegression(C=1.0, max_iter=5000, solver='lbfgs', random_state=seed)
    elif name == 'xgboost':
        numeric = 'passthrough'
        estimator = XGBClassifier(
            objective='binary:logistic', eval_metric='logloss', tree_method='hist',
            n_estimators=200, max_depth=3, learning_rate=0.05, min_child_weight=10,
            subsample=0.8, colsample_bytree=0.8, reg_lambda=5.0,
            random_state=seed, n_jobs=jobs,
        )
    else:
        raise ValueError(f'Unknown model: {name}')
    prepare = ColumnTransformer([('numeric', numeric, NUMERIC),
                                 ('categorical', categories, CATEGORICAL)], sparse_threshold=0)
    return Pipeline([('prepare', prepare), ('model', estimator)])


def score(y, probability):
    p = np.asarray(probability)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid probability')
    return {'rows': len(y), 'positives': int(np.sum(y)), 'positive_rate': float(np.mean(y)),
            'mean_probability': float(p.mean()),
            'average_precision': float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else np.nan,
            'roc_auc': float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else np.nan,
            'log_loss': float(log_loss(y, p, labels=[0, 1])),
            'brier_score': float(brier_score_loss(y, p))}


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def run(processed_root, output_root, sessions, seed=42, jobs=2, split="leave-one-race-out", min_train_races=3):
    data, sources = load_dataset(processed_root, sessions)
    X, y = feature_frame(data), data[TARGET].to_numpy()
    if split not in ['leave-one-race-out', 'forward']:
        raise ValueError('Unknown split mode')
    folds = list(forward_splits(data, min_train_races) if split == 'forward' else race_splits(data))
    expected_rows = sum(len(test) for _, _, test in folds)
    tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:6]
    folder = output_root / tag
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'models').mkdir()
    metrics, predictions, splits = [], [], []
    for held_out, train, test in folds:
        train_sessions = sorted(int(k) for k in data.iloc[train].session_key.unique())
        splits.append({'test_session': held_out, 'train_sessions': train_sessions,
                       'train_rows': len(train), 'test_rows': len(test)})
        if len(np.unique(y[train])) != 2:
            raise ValueError(f'Training races for {held_out} must contain both classes')
        base = float(y[train].mean())
        for name in ['constant', 'logistic', 'xgboost']:
            print(f'[{held_out}] {name}: train={len(train)}, test={len(test)}', flush=True)
            if name == 'constant':
                p = np.full(len(test), base)
            else:
                model = make_model(name, seed, jobs)
                with warnings.catch_warnings():
                    warnings.simplefilter('error', ConvergenceWarning)
                    model.fit(X.iloc[train], y[train])
                p = model.predict_proba(X.iloc[test])[:, 1]
                model_path = folder / 'models' / f'{name}_heldout_{held_out}.joblib'
                joblib.dump(model, model_path)
                np.testing.assert_allclose(joblib.load(model_path).predict_proba(X.iloc[test])[:, 1], p)
            metrics.append({'model': name, 'test_session': held_out,
                            'train_positive_rate': base, **score(y[test], p)})
            part = data.iloc[test][['row_id'] + IDENTITY + ['battle_id', TARGET]].copy()
            part['model'], part['probability'] = name, p
            predictions.append(part)
    per_race = pd.DataFrame(metrics)
    oof = pd.concat(predictions, ignore_index=True)
    if oof.duplicated(['model', 'row_id']).any() or len(oof) != 3 * expected_rows:
        raise AssertionError('Each row must have exactly one held-out prediction per model')
    pooled = pd.DataFrame([{'model': name, **score(part[TARGET], part.probability)}
                           for name, part in oof.groupby('model')])
    measure = ['average_precision', 'roc_auc', 'log_loss', 'brier_score']
    macro = per_race.groupby('model')[measure].mean().reset_index()
    valid_folds = per_race.groupby('model')[measure].count().add_suffix('_valid_folds').reset_index()
    macro = macro.merge(valid_folds, on='model')
    calibration = oof.assign(bin=np.minimum((oof.probability * 10).astype(int), 9))
    calibration = calibration.groupby(['model', 'bin']).agg(
        rows=(TARGET, 'size'), mean_probability=('probability', 'mean'),
        observed_rate=(TARGET, 'mean')).reset_index()
    for name, frame in [('metrics_by_race', per_race), ('metrics_macro', macro),
                        ('metrics_pooled', pooled), ('calibration', calibration)]:
        frame.to_csv(folder / f'{name}.csv', index=False, encoding='utf-8-sig')
    oof.to_parquet(folder / 'oof_predictions.parquet', index=False)
    missing = X.isna().sum().rename('missing_rows').to_frame()
    missing['missing_fraction'] = missing.missing_rows / len(X)
    missing.to_csv(folder / 'feature_missingness.csv', encoding='utf-8-sig')
    write_json(folder / 'manifest.json', {
        'status': 'complete', 'features': FEATURES, 'target': TARGET, 'sources': sources,
        'split': split, 'min_train_races': min_train_races if split == 'forward' else None,
        'evaluation_rows': expected_rows, 'folds': splits, 'random_seed': seed,
        'python': platform.python_version(), 'packages': {
            'numpy': np.__version__, 'pandas': pd.__version__, 'scikit-learn': sklearn.__version__,
            'xgboost': xgboost.__version__, 'joblib': joblib.__version__},
        'parameters': {name: {k: ('NaN' if isinstance(v, float) and not np.isfinite(v) else v)
                              for k, v in make_model(name, seed, jobs).named_steps['model'].get_params().items()}
                       for name in ['logistic', 'xgboost']},
        'limitations': [
            'Row-level metrics on automatically generated labels, not independent overtake truth.',
            'Nearby rows share events; these are not independent observations.',
            'AP and ROC AUC are undefined for single-class evaluation races; macro reports valid fold counts.',
            'Limited race sample; no hyperparameter tuning, calibration fitting or final model selection.',
            ('Earlier races only; initial training races have no held-out predictions.' if split == 'forward'
             else 'Leave-one-race-out is not chronological future-race validation.'),
            'All known labels retained, including the previously reviewed 225 positive rows.',
            'Fold models are evaluation artifacts, not a final deployed model.',
        ],
    })
    print('\nEqual-weight mean across races:')
    print(macro.to_string(index=False))
    print(f'\nReport: {folder.resolve()}')
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed-root', type=Path, default=ROOT / 'data' / 'processed')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'data' / 'processed' / 'training_reports')
    parser.add_argument('--sessions', type=int, nargs='+', default=[9472, 9480, 9488])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--split', choices=['leave-one-race-out', 'forward'], default='leave-one-race-out')
    parser.add_argument('--min-train-races', type=int, default=3)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    run(args.processed_root, args.output_root, args.sessions, args.seed, args.jobs, args.split, args.min_train_races)


if __name__ == '__main__':
    main()
