"""Regression tests: corrupt raw evidence after creating a valid label."""
from copy import deepcopy
import pandas as pd
import pytest
from app.pipeline.extract import extract_candidates
from app.pipeline.label import make_labels, validate_labels

BASE = pd.Timestamp('2024-01-01T00:00:00Z')
def at(seconds):
    return BASE + pd.Timedelta(seconds=seconds)

@pytest.fixture
def sample():
    data = {
        'race_control': [dict(date=at(0), message='SESSION STARTED'),
                         dict(date=at(500), message='SESSION ENDED')],
        'pit': [], 'overtakes': [],
        'position': [dict(driver_number=d, position=d, date=at(0)) for d in (1, 2)],
        'laps': [dict(driver_number=d, lap_number=n, date_start=at((n-1)*60),
                      lap_duration=60, is_pit_out_lap=False)
                 for d in (1, 2) for n in range(1, 8)],
        'stints': [dict(driver_number=d, lap_start=1, compound='MEDIUM', tyre_age_at_start=0)
                   for d in (1, 2)],
        'intervals': [dict(driver_number=d, date=at(s), interval=d-1,
                           gap_to_leader=d-1, session_key=1)
                      for d in (1, 2) for s in range(0, 421, 2)],
    }
    candidates, _, _ = extract_candidates(data)
    candidates = candidates[candidates.prediction_time.eq(at(80))].reset_index(drop=True)
    return data, candidates

def positive(data):
    data = deepcopy(data)
    data['overtakes'] = [dict(date=at(100), overtaking_driver_number=2, overtaken_driver_number=1)]
    data['position'] += [dict(driver_number=d, position=3-d, date=at(100)) for d in (1, 2)]
    for r in data['intervals']:
        if r['date'] >= at(100):
            r['gap_to_leader'] = 2-r['driver_number']
    return data

@pytest.mark.parametrize('success', [False, True])
def test_clean_labels(sample, success):
    data, candidates = sample
    if success: data = positive(data)
    labels = make_labels(candidates, data)
    assert labels.target_overtake_3lap.iloc[0] == int(success)
    assert validate_labels(labels, data)['violations'] == 0

@pytest.mark.parametrize('message,extra,reason', [
    ('SAFETY CAR DEPLOYED', {}, 'raw_race_control'),
    ('VIRTUAL SAFETY CAR DEPLOYED', {}, 'raw_race_control'),
    ('YELLOW', {'flag':'YELLOW','scope':'TRACK'}, 'raw_race_control'),
    ('SESSION SUSPENDED', {}, 'raw_race_control'),
    ('SESSION ENDED', {}, 'raw_session_end'),
    ('CAR 2 RETIRED', {}, 'raw_retirement'),
])
@pytest.mark.parametrize('success', [False, True])
def test_control_changes_rejected(sample, message, extra, reason, success):
    data, candidates = sample
    if success: data = positive(data)
    labels = make_labels(candidates, data)
    data['race_control'].append(dict(date=at(90), message=message, **extra))
    with pytest.raises(ValueError, match=reason): validate_labels(labels, data)

@pytest.mark.parametrize('success', [False, True])
@pytest.mark.parametrize('kind', ['pit', 'outlap', 'coverage', 'missing_lap', 'incomplete'])
def test_raw_observation_corruption(sample, kind, success):
    data, candidates = sample
    if success: data = positive(data)
    labels = make_labels(candidates, data)
    reason = 'raw_|third_completion' if kind == 'missing_lap' else 'raw_'
    if kind == 'pit': data['pit'] = [dict(driver_number=2, lap_number=2)]
    elif kind == 'outlap':
        next(r for r in data['laps'] if r['driver_number']==2 and r['lap_number']==2)['is_pit_out_lap']=True
    elif kind == 'coverage':
        data['intervals'] = [r for r in data['intervals'] if not(r['driver_number']==2 and at(82)<=r['date']<=at(98))]
    elif kind == 'missing_lap':
        data['laps'] = [r for r in data['laps'] if not(r['driver_number']==2 and r['lap_number']==2)]
    else:
        next(r for r in data['laps'] if r['driver_number']==2 and r['lap_number']==2)['lap_duration']=None
    with pytest.raises(ValueError, match=reason): validate_labels(labels, data)

def test_post_success_control_does_not_invalidate(sample):
    data, candidates = sample
    data=positive(data); labels=make_labels(candidates,data)
    data['race_control'].append(dict(date=at(110),message='SAFETY CAR DEPLOYED'))
    assert validate_labels(labels,data)['violations']==0

def test_leader_without_interval_heartbeat(sample):
    data,candidates=sample
    labels=make_labels(candidates,data)
    data['intervals']=[r for r in data['intervals'] if r['driver_number']!=1]
    assert validate_labels(labels,data)['violations']==0

def test_horizon_policy_unchanged(sample):
    data,candidates=sample;data=positive(data)
    data['laps']=[r for r in data['laps'] if r['driver_number']!=2 or r['lap_number']<4]
    labels=make_labels(candidates,data)
    assert labels.label_reason.iloc[0]=='horizon_unobserved'
