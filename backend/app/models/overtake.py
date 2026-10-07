import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OvertakeResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class OvertakeEligibilityState(int, enum.Enum):
    NEITHER = 0
    ATTACKER_ONLY = 1
    DEFENDER_ONLY = 2
    BOTH = 3


class Overtake(Base):
    __tablename__ = "overtakes"

    # =========================
    # Primary Key
    # =========================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =========================
    # Relationships
    # =========================

    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id"),
        nullable=False,
        index=True,
    )

    attacker_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id"),
        nullable=False,
        index=True,
    )

    defender_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id"),
        nullable=False,
        index=True,
    )

    # =========================
    # Race Context
    # =========================

    lap: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    track: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # 0.0 ~ 1.0
    race_progress: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # =========================
    # Gap
    # =========================

    # Seconds
    gap_at_prediction: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # =========================
    # Corner / Exit Performance
    # attacker - defender
    # =========================

    # km/h
    min_corner_speed_delta: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # km/h
    exit_speed_delta: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # acceleration delta
    # attacker - defender
    exit_acceleration_delta: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================
    # Tyre
    # =========================

    # attacker tyre age - defender tyre age
    tyre_age_diff: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    attacker_compound: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    attacker_tyre_age: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    defender_compound: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    defender_tyre_age: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================
    # Energy
    #
    # FastF1에서 실제 battery SOC를
    # 직접 제공하지 않으므로 nullable.
    #
    # 추후 실제 SOC / usable energy /
    # deployment proxy 등을 연결 가능.
    # =========================

    attacker_energy_state: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    defender_energy_state: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # attacker - defender
    energy_state_diff: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================
    # 2026 Overtake Mode Eligibility
    # =========================

    attacker_overtake_eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    defender_overtake_eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    overtake_eligibility_state: Mapped[OvertakeEligibilityState] = (
        mapped_column(
            Enum(OvertakeEligibilityState),
            nullable=False,
            default=OvertakeEligibilityState.NEITHER,
        )
    )

    # =========================
    # Relative Performance
    # attacker - defender
    # =========================

    # Seconds
    # 음수면 attacker가 qualifying에서 더 빨랐다는 식으로
    # 방향을 일관되게 유지
    qualifying_delta: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Seconds/lap 또는 추후 정의한 pace metric
    recent_race_pace_diff: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # km/h
    top_speed_diff: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================
    # Hotspot
    # =========================

    # meters
    hotspot_straight_length: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    hotspot_braking_zone_severity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ex)
    # SLOW
    # MEDIUM
    # FAST
    # CHICANE
    # HAIRPIN
    hotspot_corner_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # 0.0 ~ 1.0
    hotspot_historical_success_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================
    # Label
    # =========================

    result: Mapped[OvertakeResult | None] = mapped_column(
        Enum(OvertakeResult),
        nullable=True,
    )