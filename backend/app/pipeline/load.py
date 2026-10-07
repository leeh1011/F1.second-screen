from pathlib import Path

import pandas as pd


DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
)


def save_candidates(data, session_key):
    if data.empty:
        raise ValueError("저장할 후보가 없습니다.")

    if not data["session_key"].eq(session_key).all():
        raise ValueError("다른 경기의 데이터가 섞여 있습니다.")

    folder = DATA_DIR / str(session_key)
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / "candidates.parquet"
    temporary_path = folder / "candidates.tmp.parquet"

    data.to_parquet(
        temporary_path,
        engine="pyarrow",
        index=False,
    )
    temporary_path.replace(path)

    print(f"\n저장 완료: {path}")
    print(f"저장한 후보: {len(data)}행")

    return path


def load_candidates(session_key):
    path = DATA_DIR / str(session_key) / "candidates.parquet"

    if not path.exists():
        raise FileNotFoundError(f"저장된 후보가 없습니다: {path}")

    return pd.read_parquet(path, engine="pyarrow")