"""Chronological multi-season training with one held-out final race."""
import argparse
import hashlib
import json
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from app.pipeline.batch import ROOT, run_batch
from app.pipeline.collect import fetch_data
from app.pipeline.train import FEATURES, IDENTITY, TARGET, feature_frame, load_dataset, make_model, score, write_json

CLIP = 1e-6


def make_plan(records, calibration_races=5, years=None, test_session=None, now=None):
    if calibration_races < 1:
        raise ValueError('calibration_races must be positive')
    now = pd.Timestamp(now or datetime.now(timezone.utc))
    if now.tzinfo is None:
        raise ValueError('now must include a timezone')
    races = []
    for record in records:
        if record.get('session_name') != 'Race' or record.get('is_cancelled', False):
            continue
        if years is not None and int(record['year']) not in years:
            continue
        start = pd.to_datetime(record.get('date_start'), utc=True)
        end = pd.to_datetime(record.get('date_end'), utc=True)
        if pd.isna(start) or pd.isna(end) or start >= end:
            raise ValueError('Invalid race schedule timestamps')
        if end + pd.Timedelta(minutes=30) >= now:
            continue
        races.append(dict(record, session_key=int(record['session_key']), year=int(record['year'])))
    races.sort(key=lambda r: pd.Timestamp(r['date_start']))
    if len({r['session_key'] for r in races}) != len(races):
        raise ValueError('Duplicate session keys')
    if test_session is not None:
        matches = [i for i, r in enumerate(races) if r['session_key'] == test_session]
        if len(matches) != 1:
            raise ValueError('Requested test race is not in the completed schedule')
        races = races[:matches[0] + 1]
    if len(races) < calibration_races + 4:
        raise ValueError('Need at least three training races, calibration races and one test race')
    cut = len(races) - calibration_races - 1
    plan = []
    for i, race in enumerate(races):
        if i and pd.Timestamp(races[i-1]['date_end']) >= pd.Timestamp(race['date_start']):
            raise ValueError('Overlapping race schedule')
        item = {k: race.get(k) for k in ['session_key', 'year', 'date_start', 'date_end',
                                        'country_name', 'circuit_short_name']}
        item['round'] = i + 1
        item['role'] = 'train' if i < cut else 'calibration' if i < len(races)-1 else 'test'
        plan.append(item)
    return plan


def year_weights(data, plan, gamma=0.8):
    if not np.isfinite(gamma) or not 0 < gamma <= 1:
        raise ValueError('year_decay must be in (0, 1]')
    train_years = {r['session_key']: r['year'] for r in plan if r['role'] == 'train'}
    years = data.session_key.map(train_years)
    if years.isna().any() or data.empty:
        raise ValueError('Weights must be computed only for nonempty training data')
    reference = max(train_years.values())
    raw = np.power(gamma, reference - years.to_numpy(dtype=int))
    weights = raw / raw.mean()
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('Invalid sample weights')
    return weights


def role_indices(data, plan):
    expected = {int(r['session_key']) for r in plan}
    if set(data.session_key) != expected:
        raise ValueError('Dataset does not match the fixed season plan')
    indices = {role: np.flatnonzero(data.session_key.isin(
        [r['session_key'] for r in plan if r['role'] == role])) for role in ['train', 'calibration', 'test']}
    if any(len(v) == 0 for v in indices.values()):
        raise ValueError('Empty dataset partition')
    for earlier, later in [('train', 'calibration'), ('calibration', 'test')]:
        if data.iloc[indices[earlier]].prediction_time.max() >= data.iloc[indices[later]].prediction_time.min():
            raise ValueError('Chronological partitions overlap')
    return indices


def logit_features(probability):
    p = np.asarray(probability, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid calibration probability')
    p = np.clip(p, CLIP, 1 - CLIP)
    return (np.log(p) - np.log1p(-p)).reshape(-1, 1)


def fit_pair(name, X_train, y_train, X_cal, y_cal, jobs=2, sample_weight=None):
    if set(np.unique(y_train)) != {0, 1} or set(np.unique(y_cal)) != {0, 1}:
        raise ValueError('Training and calibration partitions each need both classes')
    base = make_model(name, seed=42, jobs=jobs)
    calibrator = LogisticRegression(C=1.0, solver='lbfgs', max_iter=5000)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        base.fit(X_train, y_train, model__sample_weight=sample_weight)
        calibrator.fit(logit_features(base.predict_proba(X_cal)[:, 1]), y_cal)
    return {'base': base, 'calibrator': calibrator, 'features': FEATURES,
            'clip': CLIP, 'method': 'regularized sigmoid on logit(p), C=1'}


def predict_pair(bundle, X):
    raw = bundle['base'].predict_proba(X)[:, 1]
    adjusted = bundle['calibrator'].predict_proba(logit_features(raw))[:, 1]
    return raw, adjusted


def reliability(predictions, by_race=False):
    data = predictions.assign(bin=np.minimum((predictions.probability * 10).astype(int), 9))
    groups = ['model', 'variant'] + (['session_key'] if by_race else []) + ['bin']
    result = data.groupby(groups).agg(rows=(TARGET, 'size'), mean_probability=('probability', 'mean'),
                                     observed_rate=(TARGET, 'mean')).reset_index()
    result['bin_lower'] = result['bin'] / 10
    result['bin_upper'] = (result['bin'] + 1) / 10
    return result


def evaluate(processed_root, output, plan, jobs=2, year_decay=0.8):
    keys = [r['session_key'] for r in plan]
    data, sources = load_dataset(processed_root, keys)
    ix = role_indices(data, plan)
    X, y = feature_frame(data), data[TARGET].to_numpy()
    train, cal, test = (ix[k] for k in ['train', 'calibration', 'test'])
    metrics, prediction_frames, parameters = [], [], {}
    weights = year_weights(data.iloc[train], plan, year_decay)
    (output / 'models').mkdir(exist_ok=True)
    for name in ['constant', 'logistic', 'xgboost']:
        print(f'{name}: train={len(train)}, calibration={len(cal)}, test={len(test)}', flush=True)
        if name == 'constant':
            variants = {'raw': np.full(len(test), np.average(y[train], weights=weights))}
        else:
            bundle = fit_pair(name, X.iloc[train], y[train], X.iloc[cal], y[cal], jobs, sample_weight=weights)
            raw, adjusted = predict_pair(bundle, X.iloc[test])
            variants = {'raw': raw, 'sigmoid': adjusted}
            path = output / 'models' / f'{name}.joblib'
            joblib.dump(bundle, path)
            restored = predict_pair(joblib.load(path), X.iloc[test])
            np.testing.assert_allclose(restored[0], raw)
            np.testing.assert_allclose(restored[1], adjusted)
            params = bundle['base'].named_steps['model'].get_params()
            parameters[name] = {
                'base': {k: ('NaN' if isinstance(v, float) and not np.isfinite(v) else v) for k, v in params.items()},
                'calibrator': bundle['calibrator'].get_params(),
                'slope': float(bundle['calibrator'].coef_[0, 0]),
                'intercept': float(bundle['calibrator'].intercept_[0]),
            }
        for variant, p in variants.items():
            part = data.iloc[test][['row_id'] + IDENTITY + ['battle_id', TARGET]].copy()
            part['model'], part['variant'], part['probability'] = name, variant, p
            prediction_frames.append(part)
            for key, frame in part.groupby('session_key'):
                metrics.append({'model': name, 'variant': variant, 'test_session': int(key),
                                **score(frame[TARGET], frame.probability)})
    predictions = pd.concat(prediction_frames, ignore_index=True)
    if predictions.duplicated(['model', 'variant', 'row_id']).any() or len(predictions) != 5 * len(test):
        raise AssertionError('Unpaired or duplicate test predictions')
    metrics = pd.DataFrame(metrics)
    columns = ['average_precision', 'roc_auc', 'log_loss', 'brier_score']
    groups = metrics.groupby(['model', 'variant'])[columns]
    macro = groups.mean().join(groups.count().add_suffix('_valid_races')).reset_index()
    pooled = pd.DataFrame([{'model': m, 'variant': v, **score(g[TARGET], g.probability)}
                           for (m, v), g in predictions.groupby(['model', 'variant'])])
    delta = []
    for name in ['logistic', 'xgboost']:
        m = metrics[metrics.model.eq(name)].set_index(['test_session', 'variant'])
        for key in sorted(m.index.get_level_values(0).unique()):
            raw, adj = m.loc[(key, 'raw')], m.loc[(key, 'sigmoid')]
            delta.append({'model': name, 'test_session': int(key),
                          **{c + '_change': adj[c] - raw[c] for c in columns}})
    for name, frame in [('metrics_by_race', metrics), ('metrics_macro', macro), ('metrics_pooled', pooled),
                        ('paired_changes', pd.DataFrame(delta)),
                        ('reliability_by_race', reliability(predictions, True)),
                        ('reliability_pooled', reliability(predictions))]:
        frame.to_csv(output / f'{name}.csv', index=False, encoding='utf-8-sig')
    predictions.to_parquet(output / 'test_predictions.parquet', index=False)
    write_json(output / 'manifest.json', {
        'status': 'complete', 'year_decay': year_decay,
        'weighting': 'Training estimator only; mean-one row weights. Calibration and evaluation unweighted.',
        'year_weights': [{'year': int(year), 'rows': int(mask.sum()),
                          'weight': float(weights[mask][0])}
                         for year in sorted({r['year'] for r in plan if r['role'] == 'train'})
                         for mask in [data.iloc[train].session_key.map(
                             {r['session_key']: r['year'] for r in plan}).eq(year).to_numpy()]],
        'plan': plan, 'features': FEATURES, 'sources': sources,
        'partitions': {role: {'rows': len(rows), 'positives': int(y[rows].sum())} for role, rows in ix.items()},
        'parameters': parameters, 'calibration_method': 'regularized sigmoid on clipped logit probability',
        'clip': CLIP, 'python': platform.python_version(), 'versions': {'numpy': np.__version__,
            'pandas': pd.__version__, 'sklearn': sklearn.__version__, 'xgboost': xgboost.__version__},
        'limitations': ['Automatic labels; correlated rows, not independent overtake trials.',
                        'No test-set tuning, model selection or refitting on calibration races.',
                        'Decay must be chosen before inspecting the test race; no automatic tuning is performed.',
                        'One held-out race is insufficient for a stable generalization estimate.',
                        'Offline eligibility and finalized records are not a causal live replay.',
                        'Calibration may worsen probability estimates on shifted race conditions.'],
    })
    print(macro.to_string(index=False))
    print(f'Report: {output.resolve()}')


def load_predictor(model_path):
    path = Path(model_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Model file not found: {path}')
    manifest = path.parent.parent / 'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8'))['status'] != 'complete':
        raise ValueError('Model report is not complete; training may have failed or be running')
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or not {'base', 'calibrator', 'features', 'clip'}.issubset(bundle):
        raise ValueError('Expected a calibrated season model bundle')
    if list(bundle['features']) != list(FEATURES) or bundle['clip'] != CLIP:
        raise ValueError('Model feature/calibration configuration differs from current code')
    for key in ('base', 'calibrator'):
        if not np.array_equal(bundle[key].classes_, [0, 1]):
            raise ValueError('Unexpected model classes')
    return bundle


def predict_overtake(predictor, features):
    X = feature_frame(pd.DataFrame([dict(features)]))
    _, adjusted = predict_pair(predictor, X)
    probability = float(adjusted[0])
    if not np.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError('Invalid prediction probability')
    return probability


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', type=int, nargs='+', default=[2024])
    parser.add_argument('--schedule', type=Path)
    parser.add_argument('--test-session', type=int)
    parser.add_argument('--calibration-races', type=int, default=5)
    parser.add_argument('--year-decay', type=float, default=0.8)
    parser.add_argument('--processed-root', type=Path, default=ROOT / 'data' / 'processed')
    parser.add_argument('--raw-root', type=Path, default=ROOT / 'data' / 'pilot_raw')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'data' / 'processed' / 'season_reports')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--prepared-only', action='store_true')
    parser.add_argument('--plan-only', action='store_true')
    args = parser.parse_args()
    if args.jobs < 1 or not 0 < args.year_decay <= 1 or args.calibration_races < 1:
        parser.error('Require jobs >= 1, calibration-races >= 1 and 0 < year-decay <= 1')
    years = sorted(set(args.years))
    if any(year < 2023 or year > datetime.now(timezone.utc).year for year in years):
        parser.error('Years must be between 2023 and the current year')
    if args.schedule:
        records = json.loads(args.schedule.read_text(encoding='utf-8-sig'))
    else:
        records = []
        for year in years:
            records.extend(fetch_data('sessions', refresh=True, year=year, session_name='Race'))
    if not isinstance(records, list):
        raise ValueError('Schedule JSON must be a list of session objects')
    if set(years) - {int(r['year']) for r in records if r.get('year') is not None}:
        raise ValueError('Schedule does not contain all requested years')
    plan = make_plan(records, args.calibration_races, years, args.test_session)
    for r in plan:
        print(f"{r['round']:02d} {r['role']:11s} {r['year']} {r['session_key']} {r['circuit_short_name']}", flush=True)
    print(f"year_decay={args.year_decay}; test_session={plan[-1]['session_key']}", flush=True)
    if args.plan_only:
        return
    out = args.output_root / 'latest'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'manifest.json', {'status': 'running', 'plan': plan, 'year_decay': args.year_decay})
    write_json(out / 'split_plan.json', plan)
    (out / 'failure.json').unlink(missing_ok=True)
    try:
        if not args.prepared_only:
            result = run_batch([r['session_key'] for r in plan], args.raw_root, args.processed_root, out)
            if result.status.ne('ok').any() or result.validation_violations.fillna(-1).ne(0).any():
                raise ValueError('Collection/validation failed: inspect comparison.csv. No race was dropped.')
        evaluate(args.processed_root, out, plan, args.jobs, args.year_decay)
    except Exception as exc:
        failure = {'status': 'failed', 'type': type(exc).__name__, 'message': str(exc), 'plan': plan}
        write_json(out / 'manifest.json', failure)
        write_json(out / 'failure.json', failure)
        raise


if __name__ == '__main__':
    main()
