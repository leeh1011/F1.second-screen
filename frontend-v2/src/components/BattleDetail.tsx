import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import type { Battle } from "@/types";
import TyreMark from "./TyreMark";

type HistoryPoint = { lap: number; probability: number | null; gap: number };

type BattleDetailProps = {
  battleId: string;
  battle: Battle | undefined; // 지금 장면의 배틀 (끝났으면 undefined)
  history: HistoryPoint[];
  onClose: () => void;
};

const lapTick = (v: number) => `${v}랩`;

function BattleDetail({ battleId, battle, history, onClose }: BattleDetailProps) {
  const first = history[0];
  const last = history[history.length - 1];

  return (
    <>
      <div className="detail-backdrop" onClick={onClose} />
      <aside className="detail-panel" aria-label="배틀 상세">
        <header className="detail-head">
          <h2 className="section-title">배틀 상세</h2>
          <button type="button" className="detail-close" onClick={onClose}>
            닫기
          </button>
        </header>

        {battle ? (
          <p className="detail-who">
            <span className="who-code">{battle.attacker_code}</span>
            <span className="detail-arrow">→</span>
            <span className="who-code">{battle.defender_code}</span>
          </p>
        ) : (
          <p className="state-note">이 배틀은 끝났어요. (추월 또는 간격 벌어짐)</p>
        )}

        <h3 className="detail-sub">3랩 내 추월 확률 (%)</h3>
        <div className="detail-chart">
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={history} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="lap" stroke="var(--sidewall)" tickFormatter={lapTick} />
              <YAxis domain={[0, 100]} stroke="var(--sidewall)" />
              <Tooltip
                contentStyle={{ background: "var(--tarmac)", border: "1px solid var(--line)" }}
                labelFormatter={(label) => `${label}랩`}
                formatter={(v) => [`${v}%`, "확률"]}
              />
              <Line
                type="monotone"
                dataKey="probability"
                stroke="var(--timing)"
                strokeWidth={3}
                dot={{ r: 4, fill: "var(--timing)" }}
                connectNulls={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <h3 className="detail-sub">간격 (초)</h3>
        <div className="detail-chart">
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={history} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="lap" stroke="var(--sidewall)" tickFormatter={lapTick} />
              <YAxis domain={[0, 2.5]} stroke="var(--sidewall)" />
              <Tooltip
                contentStyle={{ background: "var(--tarmac)", border: "1px solid var(--line)" }}
                labelFormatter={(label) => `${label}랩`}
                formatter={(v) => [`${v}초`, "간격"]}
              />
              <Line
                type="monotone"
                dataKey="gap"
                stroke="var(--ink)"
                strokeWidth={2}
                dot={{ r: 3, fill: "var(--ink)" }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {battle && (
          <>
            <h3 className="detail-sub">예측 근거</h3>
            <dl className="detail-facts">
              <dt>현재 간격</dt>
              <dd>{battle.gap.toFixed(1)}초</dd>
              <dt>간격 변화</dt>
              <dd>{first && last ? `${first.gap.toFixed(1)}초 → ${last.gap.toFixed(1)}초` : "-"}</dd>
              <dt>타이어</dt>
              <dd className="detail-tyres">
                <TyreMark tyre={battle.attacker_tyre} />
                <span>vs</span>
                <TyreMark tyre={battle.defender_tyre} />
              </dd>
              <dt>타이어 사용 차</dt>
              <dd>{battle.attacker_tyre.age - battle.defender_tyre.age}랩</dd>
            </dl>
          </>
        )}

        <p className="detail-note">
          확률은 모델 예측값이에요. 보정 전이라 실제 추월 확률과 다를 수 있어요. (배틀 {battleId})
        </p>
      </aside>
    </>
  );
}

export default BattleDetail;
