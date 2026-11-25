import type { LiveState } from "@/types";

// 알림 한 건
export type OvertakeAlert = {
  key: string;                         // 같은 알림을 두 번 보내지 않기 위한 고유값
  kind: "chance" | "overtake" | "pause" | "info";
  title: string;
  body: string;
  battleId?: string;                   // 누르면 열 배틀 (확률 알림만)
};

// 이전 장면 → 지금 장면을 비교해서 보낼 알림을 만든다.
// 화면 상태를 바꾸지 않는 순수 함수라서 화면 표시와 시스템 알림 양쪽에서 같이 쓴다.
export function computeAlerts(
  prev: LiveState | null,
  cur: LiveState,
  threshold: number,                  // 0~1 (예: 0.75)
): OvertakeAlert[] {
  if (!prev) return [];               // 첫 장면은 비교 대상이 없음
  const alerts: OvertakeAlert[] = [];

  // 1) 추월 확률이 기준을 "새로" 넘은 배틀 (이미 넘어 있던 배틀은 다시 알리지 않음)
  for (const b of cur.battles) {
    if (b.probability === null || b.probability < threshold) continue;
    const before = prev.battles.find((p) => p.battle_id === b.battle_id)?.probability ?? null;
    if (before !== null && before >= threshold) continue;

    const pct = Math.round(b.probability * 100);
    alerts.push({
      key: `chance-${b.battle_id}-${cur.lap}`,
      kind: "chance",
      title: `${b.attacker_code} → ${b.defender_code} 추월 확률 ${pct}%`,
      body: `${cur.lap}랩 · 간격 ${b.gap.toFixed(1)}초 · 모델이 3랩 안 추월 가능성을 높게 보고 있어요.`,
      battleId: b.battle_id,
    });
  }

  // 2) 이번 장면에 새로 생긴 이벤트 (추월 성공, 세이프티카 등)
  const seen = new Set(prev.events.map((e) => `${e.lap}|${e.message}`));
  for (const e of cur.events) {
    if (seen.has(`${e.lap}|${e.message}`)) continue;
    const overtake = e.message.includes("추월");
    const pause = /Safety Car|세이프티카|VSC|옐로/.test(e.message);
    alerts.push({
      key: `event-${e.lap}-${e.message}`,
      kind: overtake ? "overtake" : pause ? "pause" : "info",
      title: overtake ? "추월 발생" : pause ? "예측 일시 중지" : "경기 소식",
      body: `${e.lap}랩 · ${e.message}`,
    });
  }

  return alerts;
}
