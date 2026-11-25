import type { CSSProperties } from "react";
import type { Battle } from "@/types";
import TyreMark from "./TyreMark";
import { teamOfDriver, themeFor } from "@/lib/teams";

type BattleCardProps = {
  battle: Battle;
  prevProbability: number | null;
  featured?: boolean; // 가장 확률이 높은 배틀은 확률 블록이 팀 색으로 꽉 찬다
  season?: number; // 드라이버 코드 → 팀 매핑에 쓰는 시즌
  onSelect?: () => void; // "자세히"를 눌렀을 때 (없으면 버튼을 숨김)
  pausedLabel?: string; // SC 등으로 예측을 멈췄을 때 보여 줄 이유
};

const LANE_SECONDS = 2.5; // 레인 전체가 나타내는 간격(초)
const NEAR_SECONDS = 1.0; // 추월 기회로 보는 간격(초)

function BattleCard({
  battle, prevProbability, featured = false, season, onSelect, pausedLabel,
}: BattleCardProps) {
  const {
    attacker_code, defender_code, attacker_position,
    gap, attacker_tyre, defender_tyre, probability,
  } = battle;

  const defenderPosition = attacker_position - 1;

  // 카드 안의 강조색은 추격차 팀 색, 앞차는 앞차 팀 색
  const att = themeFor(teamOfDriver(attacker_code, season));
  const def = themeFor(teamOfDriver(defender_code, season));
  const colors = {
    "--accent": att.accent,
    "--on-accent": att.on,
    "--def": def.accent,
  } as CSSProperties;

  // 확률은 0~100 정수로 보여 주고, 직전 장면과의 차이(%p)를 계산한다.
  const percent = probability === null ? null : Math.round(probability * 100);
  const prevPercent = prevProbability === null ? null : Math.round(prevProbability * 100);
  const delta = percent !== null && prevPercent !== null ? percent - prevPercent : 0;

  // 간격 레인 위치 (0~100%)
  const gapPct = (Math.min(gap, LANE_SECONDS) / LANE_SECONDS) * 100;
  const zonePct = (NEAR_SECONDS / LANE_SECONDS) * 100;
  const near = gap <= NEAR_SECONDS;

  return (
    <article className={`battle${featured ? " battle-featured" : ""}`} style={colors}>
      <div className="battle-main">
        <div className="battle-who">
          <div className="who">
            <span className="tag tag-att">
              <span className="sr-only">추격</span>
              <span className="tag-pos">P{attacker_position}</span>
              <span className="tag-code">{attacker_code}</span>
            </span>
            <TyreMark tyre={attacker_tyre} />
          </div>
          <div className="who who-def">
            <span className="tag tag-def">
              <span className="sr-only">앞차</span>
              <span className="tag-code">{defender_code}</span>
              <span className="tag-pos">P{defenderPosition}</span>
            </span>
            <TyreMark tyre={defender_tyre} />
          </div>
        </div>

        <div
          className="lane"
          role="img"
          aria-label={`${attacker_code}와 ${defender_code}의 간격 ${gap.toFixed(1)}초`}
        >
          <span className="lane-rail" />
          <span className="lane-zone" style={{ width: `${zonePct}%` }} />
          <span
            className={`lane-link${near ? " lane-link-near" : ""}`}
            style={{ width: `${gapPct}%` }}
          />
          <span className="lane-car lane-car-att" />
          <span className="lane-car lane-car-def" style={{ left: `${gapPct}%` }} />
          <span className="lane-tick" style={{ left: `${zonePct}%` }}>1.0초</span>
          <span className="lane-gap">간격 {gap.toFixed(1)}초</span>
        </div>
      </div>

      <div className={`battle-prob${percent === null ? " battle-prob-na" : ""}`}>
        {percent === null ? (
          pausedLabel ? (
            <>
              <span className="prob-na prob-paused">예측 중지</span>
              <span className="prob-label">{pausedLabel}</span>
            </>
          ) : (
            <>
              <span className="prob-na">계산 불가</span>
              <span className="prob-label">데이터가 부족해요 (0%와 다름)</span>
            </>
          )
        ) : (
          <>
            <span className="prob-value">
              {percent}
              <span className="prob-unit">%</span>
            </span>
            <span className="prob-meter" aria-hidden="true">
              <i style={{ width: `${percent}%` }} />
            </span>
            <span className="prob-label">3랩 내 추월 확률</span>
            {delta !== 0 && (
              <span
                className="prob-delta"
                aria-label={`직전 장면보다 ${Math.abs(delta)}%p ${delta > 0 ? "상승" : "하락"}`}
              >
                {delta > 0 ? "▲" : "▼"} {Math.abs(delta)}%p
              </span>
            )}
          </>
        )}
        {onSelect && (
          <button type="button" className="battle-open" onClick={onSelect}>
            자세히
          </button>
        )}
      </div>
    </article>
  );
}

export default BattleCard;
