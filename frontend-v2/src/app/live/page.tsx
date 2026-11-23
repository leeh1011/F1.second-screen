"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import LiveHeader from "@/components/LiveHeader";
import BattleCard from "@/components/BattleCard";
import StandingsTable from "@/components/StandingsTable";
import EventFeed from "@/components/EventFeed";
import ReplayControls from "@/components/ReplayControls";
import BattleDetail from "@/components/BattleDetail";
import { getReplay } from "@/lib/api";
import type { ReplayData } from "@/types";

export default function LivePage({
  searchParams,
}: {
  searchParams: Promise<{ race?: string }>;
}) {
  // 주소의 ?race=... 값 (없으면 기본 경기)
  const { race = "2024-bahrain" } = use(searchParams);

  const [replay, setReplay] = useState<ReplayData | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [missing, setMissing] = useState(false); // 재생할 수 없는 경기

  // 데이터 불러오기 (처음 한 번)
  useEffect(() => {
    async function load() {
      const data = await getReplay(race);
      if (data) setReplay(data);
      else setMissing(true);
    }
    load();
  }, [race]);

  // 재생 중이면 3초마다 다음 장면으로
  useEffect(() => {
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

    return () => clearInterval(id);
  }, [playing, replay]);

  if (missing) {
    return (
      <div className="state-block">
        <p className="state-note">이 경기는 아직 리플레이를 준비하지 않았어요.</p>
        <Link href="/" className="btn btn-quiet">경기 다시 고르기</Link>
      </div>
    );
  }

  if (!replay) {
    return <p className="state-note">불러오는 중...</p>;
  }

  const state = replay.frames[frameIndex];

  // 지금 장면까지, 선택된 배틀의 랩별 확률·간격 기록 (아직 재생되지 않은 장면은 제외)
  const history = selectedId
    ? replay.frames.slice(0, frameIndex + 1).flatMap((frame) =>
        frame.battles
          .filter((b) => b.battle_id === selectedId)
          .map((b) => ({
            lap: frame.lap,
            probability: b.probability === null ? null : Math.round(b.probability * 100),
            gap: b.gap,
          }))
      )
    : [];

  // 지금 장면에서 선택된 배틀 (추월 등으로 끝났으면 undefined)
  const selectedBattle = state.battles.find((b) => b.battle_id === selectedId);

  // 선택된 배틀이 처음 나온 기록 (끝난 뒤에도 누가 누구를 쫓았는지 알기 위해)
  const selectedOrigin = selectedId
    ? replay.frames.flatMap((f) => f.battles).find((b) => b.battle_id === selectedId)
    : undefined;

  // 배틀이 끝났다면 그 결과 이벤트 (예: "HAM → RUS 추월 성공")
  const selectedOutcome =
    selectedOrigin && !selectedBattle
      ? state.events.find(
          (e) =>
            e.message.startsWith(`${selectedOrigin.attacker_code} → ${selectedOrigin.defender_code}`) &&
            e.message.includes("추월")
        ) ?? null
      : null;

  // SC·VSC·황색기에서는 모델이 예측하지 않는다 (학습에서도 제외한 상황)
  const PAUSE_REASON: Record<string, string> = {
    SC: "세이프티카 상황이라 예측을 잠시 멈췄어요.",
    VSC: "가상 세이프티카 상황이라 예측을 잠시 멈췄어요.",
    YELLOW: "옐로 플래그 구간이라 예측을 잠시 멈췄어요.",
  };
  const pauseReason = PAUSE_REASON[state.track_status] ?? null;

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
    <div className="live">
      <p className="mode-tag">
        <span className="mode-dot" aria-hidden="true" />
        리플레이 · 저장된 경기 기록을 실시간처럼 재생해요
      </p>
      <LiveHeader liveState={state} />
      <div className="live-grid">
        <section aria-labelledby="battles-title">
          <h2 id="battles-title" className="section-title">추월 가능성이 높은 배틀</h2>
          {pauseReason ? (
            <>
              <p className="pause-banner" role="status">
                {pauseReason} 경기가 재개되면 다시 계산해요.
              </p>
              <div className="battle-list">
                {[...state.battles]
                  .sort((a, b) => a.gap - b.gap)
                  .map((b) => (
                    <BattleCard
                      key={b.battle_id}
                      battle={b}
                      prevProbability={null}
                      onSelect={() => setSelectedId(b.battle_id)}
                      pausedLabel="경기 재개 후 다시 계산"
                    />
                  ))}
              </div>
            </>
          ) : top3.length === 0 ? (
            <p className="state-note">지금은 예측할 수 있는 배틀이 없어요.</p>
          ) : (
            <div className="battle-list">
              {top3.map((b, i) => (
                <BattleCard
                  key={b.battle_id}
                  battle={b}
                  prevProbability={prevProbability(b.battle_id)}
                  featured={i === 0}
                  onSelect={() => setSelectedId(b.battle_id)}
                />
              ))}
            </div>
          )}
        </section>
        <div className="live-side">
          <section aria-labelledby="standings-title">
            <h2 id="standings-title" className="section-title">순위</h2>
            <StandingsTable standings={state.standings} battleCodes={battleCodes} />
          </section>
          <section aria-labelledby="events-title">
            <h2 id="events-title" className="section-title">최근 이벤트</h2>
            <EventFeed events={state.events} />
          </section>
        </div>
      </div>
      <ReplayControls
        playing={playing}
        frameIndex={frameIndex}
        totalFrames={replay.frames.length}
        onTogglePlay={() => setPlaying((p) => !p)}
        onReset={() => {
          setPlaying(false);
          setFrameIndex(0);
        }}
      />
      {selectedId && (
        <BattleDetail
          battleId={selectedId}
          battle={selectedBattle}
          attackerCode={selectedOrigin?.attacker_code ?? ""}
          defenderCode={selectedOrigin?.defender_code ?? ""}
          outcome={selectedOutcome}
          pauseReason={pauseReason}
          history={history}
          lap={state.lap}
          playing={playing}
          atEnd={frameIndex === replay.frames.length - 1}
          onTogglePlay={() => setPlaying((p) => !p)}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
