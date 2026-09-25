from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.openf1_service import get_sessions, get_drivers
from app.ml.predictor import predictor_engine
from app.services.gemini_service import gemini_commentary_service

api_router = APIRouter()

class PredictRequest(BaseModel):
    gap_ahead_sec: float
    tyre_age_diff: int
    speed_diff_kph: float
    drs_active: bool

class CommentaryRequest(BaseModel):
    attacker_code: str
    defender_code: str
    probability: float
    factors: List[str]
    circuit_name: str

@api_router.get("/sessions")
async def read_sessions(year: int = Query(2024, ge=2020, le=2026)):
    sessions = await get_sessions(year)
    return {"sessions": sessions, "count": len(sessions)}

@api_router.get("/sessions/{session_key}/drivers")
async def read_drivers(session_key: int):
    drivers = await get_drivers(session_key)
    return {"drivers": drivers, "count": len(drivers)}

@api_router.post("/predict")
async def predict_overtake(req: PredictRequest):
    result = predictor_engine.predict(
        gap_ahead_sec=req.gap_ahead_sec,
        tyre_age_diff=req.tyre_age_diff,
        speed_diff_kph=req.speed_diff_kph,
        drs_active=req.drs_active,
    )
    return result

@api_router.post("/commentary")
async def generate_ai_commentary(req: CommentaryRequest):
    result = await gemini_commentary_service.generate_commentary(
        attacker_code=req.attacker_code,
        defender_code=req.defender_code,
        probability=req.probability,
        factors=req.factors,
        circuit_name=req.circuit_name,
    )
    return result
