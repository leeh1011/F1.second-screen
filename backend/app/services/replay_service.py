import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from app.core.config import settings
from app.ml.replay_features import FEATURES, feature_frame
from app.ml.serving import predict_probability

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def read_candidates(path, modified, size):
    data = pd.read_parquet(path)
    required = set(FEATURES) | {'session_key', 'battle_id', 'prediction_time',
                              'attacker_number', 'defender_number', 'battle_ready'}
    if required - set(data.columns):
        raise ValueError('Candidate columns missing')
    if not data.session_key.eq(int(Path(path).parent.name)).all():
        raise ValueError('Session mismatch')
    data = data.loc[data.battle_id.notna()].copy()
    data['prediction_time'] = pd.to_datetime(data.prediction_time, utc=True, errors='raise')
    if data.prediction_time.isna().any() or data.battle_ready.isna().any():
        raise ValueError('Missing observation time or readiness')
    if not data.battle_ready.isin([True, False]).all():
        raise ValueError('Invalid readiness flag')
    feature_frame(data)
    if data.duplicated(['battle_id', 'prediction_time']).any():
        raise ValueError('Duplicate battle observations')
    expected = str(int(Path(path).parent.name)) + '-'
    if not data.battle_id.str.startswith(expected).all():
        raise ValueError('Battle session mismatch')
    return data.sort_values(['prediction_time', 'battle_id']).reset_index(drop=True)


def candidates(session_key):
    root = settings.REPLAY_DATA_DIR
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    path = root / str(session_key) / 'candidates.parquet'
    if not path.is_file():
        raise HTTPException(404, '저장된 경기 후보 데이터가 없습니다.')
    try:
        stat = path.stat()
        return read_candidates(str(path), stat.st_mtime_ns, stat.st_size)
    except Exception as exc:
        logger.exception('Invalid replay data')
        raise HTTPException(500, '저장된 배틀 데이터를 확인해 주세요.') from exc


def predict(row, predictor):
    if not bool(row.iloc[0].battle_ready):
        raise HTTPException(422, '해당 관측 시점에는 예측 조건이 충족되지 않습니다.')
    if predictor is None:
        raise HTTPException(503, '학습된 모델이 준비되지 않았습니다.')
    try:
        return predict_probability(predictor, row.iloc[0][FEATURES].to_dict())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.exception('Replay prediction failed')
        raise HTTPException(500, '예측 처리 중 오류가 발생했습니다.') from exc
