import asyncio
import math
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.services.websocket_manager import ws_manager
from app.ml.predictor import predictor_engine
from app.services.gemini_service import gemini_commentary_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "rest": f"{settings.API_V1_STR}/sessions",
            "websocket": "/ws/live",
        },
    }

# F1 Parametric Circuit Coordinates for 2D track visualization
def calculate_circuit_coords(progress: float):
    t = (progress % 1) * 2 * math.pi
    scale_x = 0.38
    scale_y = 0.28
    r = 1 + 0.18 * math.sin(3 * t) - 0.12 * math.cos(2 * t)
    x = 0.5 + r * scale_x * math.cos(t)
    y = 0.5 + r * scale_y * math.sin(t)
    return {
        "x": round(max(0.08, min(0.92, x)), 4),
        "y": round(max(0.1, min(0.9, y)), 4),
    }

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    drivers_data = [
        {"number": 4, "code": "NOR", "team": "McLaren", "base_progress": 0.85},
        {"number": 1, "code": "VER", "team": "Red Bull Racing", "base_progress": 0.83},
        {"number": 16, "code": "LEC", "team": "Ferrari", "base_progress": 0.77},
        {"number": 81, "code": "PIA", "team": "McLaren", "base_progress": 0.72},
        {"number": 44, "code": "HAM", "team": "Ferrari", "base_progress": 0.65},
        {"number": 63, "code": "RUS", "team": "Mercedes", "base_progress": 0.58},
        {"number": 55, "code": "SAI", "team": "Williams", "base_progress": 0.49},
        {"number": 14, "code": "ALO", "team": "Aston Martin", "base_progress": 0.42},
    ]

    tyre_compounds = ["SOFT", "MEDIUM", "HARD", "SOFT", "MEDIUM", "HARD", "MEDIUM", "SOFT"]

    try:
        frame = 0
        while True:
            frame += 1
            time_offset = frame * 0.004

            # 1. Update cars track position
            cars = []
            telemetry = []

            for idx, d in enumerate(drivers_data):
                prog = (d["base_progress"] + time_offset) % 1
                coords = calculate_circuit_coords(prog)

                cars.append({
                    "driverNumber": d["number"],
                    "code": d["code"],
                    "team": d["team"],
                    "x": coords["x"],
                    "y": coords["y"],
                })

                speed_var = int(math.sin(frame * 0.2 + idx) * 9)
                base_speed = 302 if idx == 0 else 295 - idx * 2
                speed = max(260, min(338, base_speed + speed_var))

                telemetry.append({
                    "driverNumber": d["number"],
                    "code": d["code"],
                    "speedKph": speed,
                    "tyre": tyre_compounds[idx],
                    "tyreAgeLaps": 8 + idx * 3,
                    "gapAheadSeconds": None if idx == 0 else round(idx * 0.45 + math.sin(frame * 0.1) * 0.08, 3),
                    "lastLapSeconds": round(74.15 + idx * 0.18, 3),
                })

            # 2. ML Overtake Model Inference
            attacker = "NOR"
            defender = "VER"
            gap_sec = round(max(0.12, 0.42 + 0.15 * math.sin(frame * 0.1)), 3)
            tyre_diff = 13
            speed_diff = round(4.2 + math.cos(frame * 0.15) * 3, 1)
            drs_active = True

            ml_result = predictor_engine.predict(
                gap_ahead_sec=gap_sec,
                tyre_age_diff=tyre_diff,
                speed_diff_kph=speed_diff,
                drs_active=drs_active,
            )

            # 3. Gemini AI Commentary Generation
            commentary = await gemini_commentary_service.generate_commentary(
                attacker_code=attacker,
                defender_code=defender,
                probability=ml_result["success_probability"],
                factors=ml_result["factors"],
                circuit_name="Circuit de Monaco",
            )

            payload = {
                "sessionName": "FORMULA 1 MONACO GRAND PRIX 2026 (FASTAPI LIVE)",
                "circuitName": "Circuit de Monaco",
                "currentLap": 49,
                "totalLaps": 78,
                "status": "live",
                "cars": cars,
                "telemetry": telemetry,
                "overtake": {
                    "attackerCode": attacker,
                    "defenderCode": defender,
                    "successProbability": ml_result["success_probability"],
                    "factors": ml_result["factors"],
                },
                "commentary": commentary,
            }

            await websocket.send_json(payload)
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Loop Error: {e}")
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
