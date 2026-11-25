"""Serving-only adapter; leaves the evaluated training pipeline unchanged."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.replay_features import feature_frame
from app.pipeline.season import load_predictor, predict_pair


def load_model(path, variant='raw'):
    if variant not in ('raw', 'sigmoid'):
        raise ValueError('Unknown probability variant')
    path = Path(path).resolve()
    metadata = json.loads((path.parent.parent / 'manifest.json').read_text(encoding='utf-8-sig'))
    if metadata.get('status') != 'complete':
        raise ValueError('Model evaluation report is incomplete')
    bundle = load_predictor(path)
    bundle['inference_variant'] = variant
    bundle['session_roles'] = {int(r['session_key']): r['role'] for r in metadata['plan']}
    bundle['model_name'] = path.stem
    return bundle


def predict_probability(bundle, features):
    frame = feature_frame(pd.DataFrame([dict(features)]))
    required = ['gap', 'attacker_position', 'defender_position', 'attacker_lap',
                'defender_lap', 'battle_age_seconds']
    if frame[required].isna().any().any():
        raise ValueError('예측에 필요한 간격·순위·랩·배틀 이력이 부족합니다.')
    row = frame.iloc[0]
    for key in ['attacker_position', 'defender_position', 'attacker_lap', 'defender_lap']:
        if row[key] < 1 or row[key] != int(row[key]):
            raise ValueError('순위와 랩은 양의 정수여야 합니다.')
    if row.gap < 0 or row.attacker_position != row.defender_position + 1 or row.battle_age_seconds < 8:
        raise ValueError('앞차와의 배틀 예측 조건이 충족되지 않습니다.')
    if bundle['inference_variant'] == 'raw':
        probability = float(bundle['base'].predict_proba(frame)[0, 1])
    else:
        probability = float(predict_pair(bundle, frame)[1][0])
    if not np.isfinite(probability) or not 0 <= probability <= 1:
        raise RuntimeError('Invalid model probability')
    return probability
