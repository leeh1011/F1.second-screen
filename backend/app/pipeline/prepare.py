import pandas as pd


def attach_lap_numbers(candidates, laps):
    result = pd.DataFrame(candidates)

    if result.empty:
        raise ValueError("후보 데이터가 없습니다.")

    result["prediction_time"] = pd.to_datetime(
        result["prediction_time"],
        utc=True,
        format="mixed",
    )

    lap_data = pd.DataFrame(laps)[
        ["driver_number", "lap_number", "date_start"]
    ].copy()

    lap_data["date_start"] = pd.to_datetime(
        lap_data["date_start"],
        utc=True,
        format="mixed",
        errors="coerce",
    )

    lap_data = lap_data.dropna(
        subset=["driver_number", "lap_number", "date_start"]
    )

    lap_data["driver_number"] = lap_data["driver_number"].astype("int64")

    for role in ("attacker", "defender"):
        driver_column = f"{role}_number"
        lap_column = f"{role}_lap"
        start_column = f"{role}_lap_start"

        right = lap_data.rename(columns={
            "driver_number": driver_column,
            "lap_number": lap_column,
            "date_start": start_column,
        })

        if right.duplicated([driver_column, start_column]).any():
            raise ValueError("같은 차량·시각에 랩 시작 기록이 중복됩니다.")

        result[driver_column] = result[driver_column].astype("int64")

        result = pd.merge_asof(
            result.sort_values("prediction_time"),
            right.sort_values(start_column),
            left_on="prediction_time",
            right_on=start_column,
            by=driver_column,
            direction="backward",
        )

    result["seconds_since_lap_start"] = (
        result["prediction_time"] - result["attacker_lap_start"]
    ).dt.total_seconds()

    return result

def attach_tyre_features(prepared, stints):
    result = prepared.copy()

    stint_data = pd.DataFrame(stints)[
        [
            "driver_number",
            "lap_start",
            "compound",
            "tyre_age_at_start",
        ]
    ].copy()

    stint_data = stint_data.dropna(
        subset=["driver_number", "lap_start"]
    )

    stint_data["driver_number"] = stint_data["driver_number"].astype("int64")
    stint_data["lap_start"] = stint_data["lap_start"].astype("int64")
    stint_data["tyre_age_at_start"] = pd.to_numeric(
        stint_data["tyre_age_at_start"],
        errors="coerce",
    )

    if stint_data.duplicated(["driver_number", "lap_start"]).any():
        raise ValueError("같은 차량·시작 랩에 스틴트가 중복됩니다.")

    for role in ("attacker", "defender"):
        driver_column = f"{role}_number"
        lap_column = f"{role}_lap"
        start_column = f"{role}_stint_start"
        initial_age_column = f"{role}_initial_tyre_age"
        compound_column = f"{role}_compound"
        age_column = f"{role}_tyre_age"

        if result[lap_column].isna().any():
            raise ValueError("랩 번호 결측을 먼저 처리해야 합니다.")

        result[lap_column] = result[lap_column].astype("int64")

        right = stint_data.rename(columns={
            "driver_number": driver_column,
            "lap_start": start_column,
            "compound": compound_column,
            "tyre_age_at_start": initial_age_column,
        })

        result = pd.merge_asof(
            result.sort_values(lap_column),
            right.sort_values(start_column),
            left_on=lap_column,
            right_on=start_column,
            by=driver_column,
            direction="backward",
        )

        result[age_column] = (
            result[initial_age_column]
            + result[lap_column]
            - result[start_column]
        )

        transition_lap = (
            (result[start_column] > 1)
            & (result[lap_column] == result[start_column])
        )

        result.loc[transition_lap, compound_column] = None
        result.loc[transition_lap, age_column] = float("nan")

    result["tyre_age_diff"] = (
        result["attacker_tyre_age"]
        - result["defender_tyre_age"]
    )

    return result.sort_values("prediction_time").reset_index(drop=True)