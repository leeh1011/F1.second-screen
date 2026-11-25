import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.api.replay import PredictionRequest, PredictionResponse, predict_observation, router
from app.core.config import settings
from app.ml.serving import load_model, predict_probability

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


class OvertakeFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    gap: float | None
    attacker_position: float | None
    defender_position: float | None
    attacker_lap: float | None
    defender_lap: float | None
    seconds_since_lap_start: float | None
    attacker_tyre_age: float | None
    defender_tyre_age: float | None
    tyre_age_diff: float | None
    attacker_recent_pace: float | None
    defender_recent_pace: float | None
    recent_race_pace_diff: float | None
    attacker_pace_lap_count: float | None
    defender_pace_lap_count: float | None
    battle_age_seconds: float | None
    time_within_1_sec: float | None
    gap_mean_last_lap: float | None
    gap_trend_last_lap: float | None
    gap_1_lap_ago: float | None
    gap_history_complete: float | None
    gap_history_window_seconds: float | None
    defender_gap_ahead: float | None
    defender_in_train: float | None
    defender_is_leader: float | None
    attacker_compound: str | None
    defender_compound: str | None


class OvertakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: OvertakeFeatures


class OvertakeResponse(BaseModel):
    probability: float = Field(ge=0, le=1)
    calibrated: bool
    model: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.overtake_predictor = None
    app.state.overtake_model = ""
    configured = settings.OVERTAKE_MODEL_PATH
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        try:
            app.state.overtake_predictor = load_model(path, settings.OVERTAKE_MODEL_VARIANT)
            app.state.overtake_model = path.stem
        except Exception:
            logger.exception("Failed to load OVERTAKE_MODEL_PATH; prediction will return 503")
    else:
        logger.warning("OVERTAKE_MODEL_PATH is not set; prediction will return 503")
    yield
    app.state.overtake_predictor = None


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/docs"}


@app.get("/api/health")
def health():
    predictor = getattr(app.state, 'overtake_predictor', None)
    return {"status": "ok", "prediction_ready": predictor is not None,
            "model": getattr(app.state, 'overtake_model', ''),
            "variant": predictor['inference_variant'] if predictor is not None else None}


@app.post("/api/prediction/overtake", response_model=PredictionResponse | OvertakeResponse)
def predict(body: PredictionRequest | OvertakeRequest, request: Request):
    predictor = getattr(request.app.state, 'overtake_predictor', None)
    model_name = getattr(request.app.state, 'overtake_model', '')
    if isinstance(body, PredictionRequest):
        return predict_observation(body, predictor, model_name)
    if predictor is None:
        raise HTTPException(503, '학습된 모델이 준비되지 않았습니다.')
    try:
        probability = predict_probability(predictor, body.features.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.exception('Feature prediction failed')
        raise HTTPException(500, '예측 처리 중 오류가 발생했습니다.') from exc
    return OvertakeResponse(probability=probability, calibrated=predictor['inference_variant'] == 'sigmoid', model=model_name)
