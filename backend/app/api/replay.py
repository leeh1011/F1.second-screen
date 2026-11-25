from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.ml.replay_features import TARGET
from app.services.replay_service import candidates, predict

router = APIRouter(prefix='/api', tags=['replay'])


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    battle_id: str = Field(pattern=r'^[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*$', max_length=80)
    prediction_time: AwareDatetime


class PredictionResponse(BaseModel):
    battle_id: str
    prediction_time: datetime
    calibrated: bool
    variant: str
    data_role: str
    model: str
    target: str = TARGET
    probability: float = Field(ge=0, le=1)


@router.get('/races/{race_id}/battles')
def list_battles(race_id: int, offset: int = Query(0, ge=0), limit: int = Query(500, ge=1, le=2000), ready_only: bool = False):
    if race_id <= 0:
        raise HTTPException(422, 'race_id는 양수여야 합니다.')
    data = candidates(race_id)
    if ready_only:
        data = data.loc[data.battle_ready.eq(True)]
    columns = ['battle_id', 'prediction_time', 'attacker_number', 'defender_number',
               'attacker_lap', 'defender_lap', 'gap', 'attacker_compound',
               'defender_compound', 'attacker_tyre_age', 'defender_tyre_age', 'battle_ready']
    items = []
    for row in data.iloc[offset:offset + limit][columns].to_dict('records'):
        row = {key: None if pd.isna(value) else value for key, value in row.items()}
        row['prediction_time'] = row['prediction_time'].isoformat()
        items.append(row)
    next_offset = offset + len(items)
    return {'race_id': race_id, 'session_key': race_id, 'items': items,
            'total': len(data), 'next_offset': next_offset if next_offset < len(data) else None}


def predict_observation(request: PredictionRequest, predictor, model_name):
    session_key = int(request.battle_id.split('-')[0])
    data = candidates(session_key)
    selected = data.loc[data.battle_id.eq(request.battle_id)
                        & data.prediction_time.eq(pd.Timestamp(request.prediction_time))]
    if selected.empty:
        raise HTTPException(404, '배틀 또는 관측 시각을 찾을 수 없습니다.')
    probability = predict(selected, predictor)
    return PredictionResponse(battle_id=request.battle_id,
                              prediction_time=selected.iloc[0].prediction_time.to_pydatetime(),
                              probability=probability, model=model_name,
                              calibrated=predictor['inference_variant'] == 'sigmoid',
                              variant=predictor['inference_variant'],
                              data_role=predictor['session_roles'].get(session_key, 'unseen'))
