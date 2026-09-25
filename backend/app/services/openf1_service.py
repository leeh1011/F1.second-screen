import httpx
from typing import List, Dict, Any, Optional

OPENF1_BASE_URL = "https://api.openf1.org/v1"

async def get_sessions(year: int = 2024) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{OPENF1_BASE_URL}/sessions?year={year}")
            if res.status_code == 200:
                data = res.json()
                data.sort(key=lambda x: x.get("date_start", ""))
                return data
            return []
        except Exception as e:
            print(f"Error fetching OpenF1 sessions: {e}")
            return []

async def get_drivers(session_key: int) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{OPENF1_BASE_URL}/drivers?session_key={session_key}")
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            print(f"Error fetching OpenF1 drivers for session {session_key}: {e}")
            return []

async def get_car_data(session_key: int) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{OPENF1_BASE_URL}/car_data?session_key={session_key}")
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            print(f"Error fetching OpenF1 car_data for session {session_key}: {e}")
            return []

async def get_positions(session_key: int) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{OPENF1_BASE_URL}/position?session_key={session_key}")
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            print(f"Error fetching OpenF1 positions for session {session_key}: {e}")
            return []
