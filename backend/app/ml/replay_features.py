import numpy as np
import pandas as pd

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

