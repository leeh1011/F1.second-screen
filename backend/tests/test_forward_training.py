import numpy as np
import pandas as pd
import pytest
from app.pipeline.train import forward_splits
from app.pipeline.expand import select_races


def chronological():
    return pd.DataFrame({'session_key': [90, 90, 5, 5, 30, 30, 1, 1],
                         'prediction_time': pd.to_datetime([
                             '2024-01-01', '2024-01-02', '2024-02-01', '2024-02-02',
                             '2024-03-01', '2024-03-02', '2024-04-01', '2024-04-02'], utc=True)})


def test_forward_uses_dates_not_session_numbers():
    data = chronological()
    folds = list(forward_splits(data, 2))
    assert [k for k, _, _ in folds] == [30, 1]
    for key, train, test in folds:
        assert data.iloc[train].prediction_time.max() < data.iloc[test].prediction_time.min()
        assert key not in set(data.iloc[train].session_key)
    assert set(np.concatenate([test for _, _, test in folds])) == {4, 5, 6, 7}
    assert len(folds[1][1]) > len(folds[0][1])


def test_forward_rejects_overlapping_races():
    data = chronological()
    data.loc[1, 'prediction_time'] = pd.Timestamp('2024-02-03', tz='UTC')
    with pytest.raises(ValueError, match='overlap'):
        list(forward_splits(data, 2))


@pytest.mark.parametrize('minimum', [1, 4, 5])
def test_forward_requires_training_and_test_races(minimum):
    with pytest.raises(ValueError):
        list(forward_splits(chronological(), minimum))


def test_schedule_selection_excludes_sprints_cancelled_and_future():
    records = [{'year': 2024, 'session_name': 'Race', 'session_key': i,
                'date_start': f'2024-0{i}-01T00:00:00Z',
                'date_end': f'2024-0{i}-02T00:00:00Z'} for i in range(1, 7)]
    records += [{**records[0], 'session_key': 10, 'session_name': 'Sprint'},
                {**records[0], 'session_key': 11, 'is_cancelled': True}]
    assert [r['session_key'] for r in select_races(records[::-1], 2024, 4, '2024-05-01T00:00:00Z')] == [1, 2, 3, 4]
    with pytest.raises(ValueError):
        select_races(records, 2024, 6, '2024-05-01T00:00:00Z')


@pytest.mark.parametrize('vsc_ending', [False, True])
def test_sc_supersedes_vsc_but_stays_neutral_until_sc_ends(vsc_ending):
    from app.pipeline.extract import build_control
    messages = ['SESSION STARTED', 'VIRTUAL SAFETY CAR DEPLOYED']
    if vsc_ending:
        messages.append('VSC ENDING')
    messages += ['SAFETY CAR DEPLOYED', 'TRACK CLEAR', 'SAFETY CAR IN THIS LAP',
                 'TRACK CLEAR', 'DRS ENABLED']
    rows = [{'date': pd.Timestamp('2024-01-01', tz='UTC') + pd.Timedelta(seconds=i),
             'message': msg, 'scope': 'TRACK', 'flag': 'CLEAR' if msg == 'TRACK CLEAR' else ''}
            for i, msg in enumerate(messages)]
    events, unresolved = build_control(rows)
    first_clear = messages.index('TRACK CLEAR')
    assert all(e['neutralized'] for e in events[1:first_clear + 2])
    assert not events[-2]['neutralized']
    assert not unresolved


def test_drs_does_not_silently_end_unresolved_vsc():
    from app.pipeline.extract import build_control
    rows = [{'date': pd.Timestamp('2024-01-01', tz='UTC') + pd.Timedelta(seconds=i), 'message': msg}
            for i, msg in enumerate(['SESSION STARTED', 'VIRTUAL SAFETY CAR DEPLOYED', 'DRS ENABLED'])]
    events, unresolved = build_control(rows)
    assert events[-1]['neutralized'] and unresolved


def test_single_class_test_race_keeps_probability_metrics():
    from app.pipeline.train import score
    for target in [0, 1]:
        result = score(np.full(4, target), np.full(4, .2))
        assert np.isnan(result['average_precision']) and np.isnan(result['roc_auc'])
        assert np.isfinite(result['log_loss'])
        assert result['brier_score'] == pytest.approx((.2 - target)**2)
