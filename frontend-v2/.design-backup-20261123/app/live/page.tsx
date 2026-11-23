"use client";

import { useEffect, useState } from "react";
import LiveHeader from "@/components/LiveHeader";
import BattleCard from "@/components/BattleCard";
import StandingsTable from "@/components/StandingsTable";
import EventFeed from "@/components/EventFeed";
import ReplayControls from "@/components/ReplayControls";
import { getReplay } from "@/lib/api";
import type { ReplayData } from "@/types";

export default function LivePage() {
  const [replay, setReplay] = useState<ReplayData | null>(null);   // ①
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  // 데이터 불러오기 (처음 한 번)
  useEffect(() => {                                                // ②
    async function load() {
      setReplay(await getReplay());
    }
    load();
  }, []);

  // 재생 중이면 3초마다 다음 장면으로
  useEffect(() => {                                                // ③
    if (!playing || !replay) return;

    const lastIndex = replay.frames.length - 1;
    const id = setInterval(() => {
      setFrameIndex((i) => {
        if (i >= lastIndex) {          // 마지막이면 멈춤
          setPlaying(false);
          return i;
        }
        return i + 1;                  // 아니면 다음 장면
      });
    }, 3000);

    return () => clearInterval(id);                                // ④
  }, [playing, replay]);

  if (!replay) {
    return <p>불러오는 중...</p>;
  }

  const state = replay.frames[frameIndex];                         // ⑤

  const prevState = frameIndex > 0 ? replay.frames[frameIndex - 1] : null;

  // 이전 장면에서 같은 배틀의 확률 찾기 (없으면 null)
  function prevProbability(battleId: string): number | null {
    const prev = prevState?.battles.find((b) => b.battle_id === battleId);
    return prev?.probability ?? null;
  }

  const top3 = state.battles
    .filter((b) => b.probability !== null)
    .sort((a, b) => (b.probability ?? 0) - (a.probability ?? 0))
    .slice(0, 3);
  const battleCodes = top3.flatMap((b) => [b.attacker_code, b.defender_code]);

  return (
    <div>
      <ReplayControls                                              // ⑥
        playing={playing}
        frameIndex={frameIndex}
        totalFrames={replay.frames.length}
        onTogglePlay={() => setPlaying((p) => !p)}
        onReset={() => {
          setPlaying(false);
          setFrameIndex(0);
        }}
      />
      <LiveHeader liveState={state} />
      <div className="battle-list">
        {top3.map((b) => (
          <BattleCard key={b.battle_id} battle={b} prevProbability={prevProbability(b.battle_id)} />
        ))}
      </div>
      <h3>순위표</h3>
      <StandingsTable standings={state.standings} battleCodes={battleCodes} />
      <h3>최근 이벤트</h3>
      <EventFeed events={state.events} />
    </div>
  );
}