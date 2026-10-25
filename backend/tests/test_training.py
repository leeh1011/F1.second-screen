import numpy as np
import pandas as pd
import pytest
from app.pipeline.train import (FEATURES, NUMERIC, TARGET, feature_frame, load_dataset,
                                make_model, race_splits, score)


def sample():
    data = pd.DataFrame({name: np.arange(12, dtype=float) for name in NUMERIC})
    data['attacker_compound'] = 'MEDIUM'
    data['defender_compound'] = 'HARD'
    data['session_key'] = np.repeat([9472, 9480, 9488], 4)
    data['attacker_number'] = 4
    data['defender_number'] = 14
    data['prediction_time'] = pd.date_range('2024-01-01', periods=12, freq='s', tz='UTC')
    data['battle_id'] = ['battle-' + str(key) for key in data.session_key]
    data['battle_ready'] = True
    data['offline_eligible'] = True
    data['label_version'] = 'v2-gap-evidence'
    data[TARGET] = pd.Series([0, 1, 0, 1] * 3, dtype='Int64')
    return data


def test_allowlist_excludes_future_and_identity():
    data = sample()
    data['label_event_time'] = 'future'
    X = feature_frame(data)
    assert len(FEATURES) == len(set(FEATURES)) == 26
    assert list(X) == FEATURES
    assert not set(X) & {TARGET, 'label_event_time', 'session_key', 'offline_eligible', 'battle_id'}


def test_folds_keep_entire_race_and_battle_together():
    data = sample()
    seen = []
    for key, train, test in race_splits(data):
        assert set(data.iloc[test].session_key) == {key}
        assert key not in set(data.iloc[train].session_key)
        assert not set(data.iloc[train].battle_id) & set(data.iloc[test].battle_id)
        seen.extend(test)
    assert sorted(seen) == list(range(len(data)))


@pytest.mark.parametrize('name', ['logistic', 'xgboost'])
def test_train_only_preprocessing_missing_and_unseen_category(name):
    data = sample()
    data.loc[:7, 'gap'] = [1., 2., np.nan, 2., 1., 2., 1., 2.]
    data.loc[8:, 'gap'] = 10000.
    data.loc[:7, 'gap_mean_last_lap'] = np.nan
    data.loc[8:, 'attacker_compound'] = 'SOFT'
    X = feature_frame(data)
    model = make_model(name, jobs=1).fit(X.iloc[:8], data[TARGET].iloc[:8].astype(int))
    prep = model.named_steps['prepare']
    categories = prep.named_transformers_['categorical'].named_steps['encode'].categories_
    assert 'SOFT' not in categories[0]
    if name == 'logistic':
        imputer = prep.named_transformers_['numeric'].named_steps['impute']
        assert imputer.statistics_[NUMERIC.index('gap')] == 2.
    else:
        transformed = prep.transform(X.iloc[:8])
        assert np.isnan(transformed[:, NUMERIC.index('gap_mean_last_lap')]).all()
    p = model.predict_proba(X.iloc[8:])[:, 1]
    assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()


def write_sample(root, data):
    for key, frame in data.groupby('session_key'):
        folder = root / str(key)
        folder.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(folder / 'labeled_3lap_v2.parquet', index=False)


def test_loader_removes_only_unknown_targets(tmp_path):
    data = sample()
    data.loc[0, TARGET] = pd.NA
    write_sample(tmp_path, data)
    selected, _ = load_dataset(tmp_path, [9472, 9480, 9488])
    assert len(selected) == 11
    assert selected[TARGET].sum() == 6


@pytest.mark.parametrize('problem', ['duplicate', 'invalid_target', 'ineligible', 'wrong_version'])
def test_loader_rejects_invalid_data(tmp_path, problem):
    data = sample()
    if problem == 'duplicate':
        data = pd.concat([data, data.iloc[:1]])
    elif problem == 'invalid_target':
        data.loc[0, TARGET] = 2
    elif problem == 'ineligible':
        data.loc[0, 'offline_eligible'] = False
    else:
        data.loc[0, 'label_version'] = 'unknown'
    write_sample(tmp_path, data)
    with pytest.raises(ValueError):
        load_dataset(tmp_path, [9472, 9480, 9488])


def test_constant_baseline_metrics():
    result = score(np.array([0, 0, 0, 1]), np.full(4, .25))
    assert result['average_precision'] == .25
    assert result['roc_auc'] == .5
    assert result['brier_score'] == .1875
