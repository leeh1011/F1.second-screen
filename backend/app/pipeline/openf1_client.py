import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "https://api.openf1.org/v1"
CACHE_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "openf1"
    / "cache"
)

_last_request_time = None


def fetch_data(endpoint, refresh=False, **params):
    global _last_request_time

    query = urlencode(sorted(params.items()))
    url = f"{BASE_URL}/{endpoint}?{query}"
    cache_key = hashlib.sha256(url.encode()).hexdigest()[:20]
    cache_path = CACHE_DIR / endpoint / f"{cache_key}.json"

    if cache_path.exists() and not refresh:
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))

            if not isinstance(data, list):
                raise ValueError("캐시 데이터가 리스트가 아닙니다.")

            print(f"[캐시] {endpoint}: {len(data)}건")
            return data

        except (OSError, ValueError):
            print(f"[캐시 읽기 실패] {endpoint}: 다시 다운로드합니다.")

    for attempt in range(4):
        if _last_request_time is not None:
            wait = 2.1 - (time.monotonic() - _last_request_time)

            if wait > 0:
                time.sleep(wait)

        _last_request_time = time.monotonic()

        try:
            with urlopen(url, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))

            if not isinstance(data, list):
                raise ValueError("API 응답이 리스트가 아닙니다.")

            break

        except HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code < 600

            if not retryable or attempt == 3:
                raise

            delay = 5 * (attempt + 1)

            if error.code == 429:
                delay = max(delay, 60)

            print(f"[재시도] {endpoint}: HTTP {error.code}, {delay}초 대기")
            time.sleep(delay)

        except (URLError, TimeoutError):
            if attempt == 3:
                raise

            delay = 5 * (attempt + 1)
            print(f"[재시도] {endpoint}: 연결 오류, {delay}초 대기")
            time.sleep(delay)

    cache_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = cache_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(cache_path)

    print(f"[다운로드] {endpoint}: {len(data)}건")
    return data


def get_sessions(year, country_name, session_name="Race", refresh=False):
    return fetch_data(
        "sessions",
        refresh=refresh,
        year=year,
        country_name=country_name,
        session_name=session_name,
    )


def get_drivers(session_key, refresh=False):
    return fetch_data(
        "drivers",
        refresh=refresh,
        session_key=session_key,
    )


def get_intervals(session_key, driver_number=None, refresh=False):
    params = {"session_key": session_key}

    if driver_number is not None:
        params["driver_number"] = driver_number

    return fetch_data("intervals", refresh=refresh, **params)


def get_positions(session_key, refresh=False):
    return fetch_data(
        "position",
        refresh=refresh,
        session_key=session_key,
    )


def get_laps(session_key, refresh=False):
    return fetch_data(
        "laps", refresh=refresh, session_key=session_key
    )


def get_stints(session_key, refresh=False):
    return fetch_data(
        "stints", refresh=refresh, session_key=session_key
    )


def get_pit(session_key, refresh=False):
    return fetch_data(
        "pit", refresh=refresh, session_key=session_key
    )


def get_race_control(session_key, refresh=False):
    return fetch_data(
        "race_control", refresh=refresh, session_key=session_key
    )


def get_overtakes(session_key, refresh=False):
    return fetch_data(
        "overtakes", refresh=refresh, session_key=session_key
    )


def get_race_data(session_key, refresh=False):
    loaders = {
        "drivers": get_drivers,
        "intervals": get_intervals,
        "position": get_positions,
        "laps": get_laps,
        "stints": get_stints,
        "pit": get_pit,
        "race_control": get_race_control,
        "overtakes": get_overtakes,
    }

    return {
        name: loader(session_key, refresh=refresh)
        for name, loader in loaders.items()
    }