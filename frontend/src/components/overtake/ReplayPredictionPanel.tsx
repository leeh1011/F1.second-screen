"use client";

import { useEffect, useState } from "react";
import { ProbabilityGauge } from "@/components/overtake/ProbabilityGauge";
import { fetchBattles, fetchPrediction, type BattlePage, type ReplayPrediction } from "@/lib/api/replay";

export function ReplayPredictionPanel({ sessionKey }: { sessionKey: number | null }) {
  const [offset, setOffset] = useState(0);
  const [index, setIndex] = useState(0);
  const [page, setPage] = useState<(BattlePage & { offset: number }) | null>(null);
  const [prediction, setPrediction] = useState<{ key: string; value: ReplayPrediction } | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const [retry, setRetry] = useState(0);
  const currentPage = page?.offset === offset ? page : null;
  const row = currentPage?.items[index];
  const rowKey = row ? `${row.battle_id}/${row.prediction_time}` : "";
  const visiblePrediction = prediction?.key === rowKey ? prediction.value : null;

  useEffect(() => {
    if (sessionKey === null) return;
    const controller = new AbortController();
    setPageLoading(true);
    setError("");
    setPrediction(null);
    fetchBattles(sessionKey, offset, controller.signal).then((data) => {
      if (controller.signal.aborted) return;
      setPage({ ...data, offset });
      setIndex(0);
      if (data.items.length === 0) setPlaying(false);
    }).catch((reason: unknown) => {
      if (controller.signal.aborted) return;
      setPage(null);
      setPlaying(false);
      setError(reason instanceof Error ? reason.message : "관측 목록을 불러오지 못했습니다.");
    }).finally(() => {
      if (!controller.signal.aborted) setPageLoading(false);
    });
    return () => controller.abort();
  }, [sessionKey, offset, retry]);

  useEffect(() => {
    if (!row || pageLoading) return;
    const controller = new AbortController();
    setPredictionLoading(true);
    setPrediction(null);
    setError("");
    fetchPrediction(row, controller.signal).then((value) => {
      if (!controller.signal.aborted) setPrediction({ key: rowKey, value });
    }).catch((reason: unknown) => {
      if (controller.signal.aborted) return;
      setPlaying(false);
      setError(reason instanceof Error ? reason.message : "예측값을 불러오지 못했습니다.");
    }).finally(() => {
      if (!controller.signal.aborted) setPredictionLoading(false);
    });
    return () => controller.abort();
  }, [row, rowKey, pageLoading]);

  useEffect(() => {
    if (!playing || pageLoading || predictionLoading || !visiblePrediction || !currentPage || error) return;
    const timer = window.setTimeout(() => {
      if (index + 1 < currentPage.items.length) setIndex(index + 1);
      else if (currentPage.next_offset !== null) setOffset(currentPage.next_offset);
      else setPlaying(false);
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [playing, pageLoading, predictionLoading, visiblePrediction, currentPage, index, error]);

  const buttonClass = "rounded border border-white/20 px-3 py-1.5 text-xs disabled:opacity-30";
  return (
    <section className="space-y-4 rounded-2xl border border-white/10 bg-zinc-900/80 p-5">
      <h2 className="text-sm font-bold text-amber-400">저장 배틀 · 3랩 이내 추월 확률</h2>
      <p className="text-xs text-zinc-400">선택한 관측 시점의 앞차를 현재 랩 포함 3랩 이내 추월할 확률입니다. 아래 관측 재생은 지도·텔레메트리 시각과 별개입니다.</p>
      {sessionKey === null && <p className="text-sm">경기를 선택해 주세요.</p>}
      {pageLoading && <p role="status" className="text-sm">저장 관측을 불러오는 중…</p>}
      {error && <div role="alert" className="space-y-2 text-sm text-amber-300">
        <p>{error}</p>
        <button className={buttonClass} onClick={() => { setPlaying(false); setRetry((value) => value + 1); }}>다시 시도</button>
      </div>}
      {!pageLoading && currentPage?.items.length === 0 && <p className="text-sm text-zinc-400">예측 조건을 충족하는 저장 관측이 없습니다.</p>}
      {!pageLoading && row && currentPage && <>
        <label className="block text-xs text-zinc-400">
          관측 선택 ({offset + index + 1} / {currentPage.total})
          <select aria-label="배틀 관측 선택" className="mt-2 w-full rounded bg-zinc-950 p-2 text-zinc-100" value={index}
            onChange={(event) => { setPlaying(false); setIndex(Number(event.target.value)); }}>
            {currentPage.items.map((item, itemIndex) => <option key={`${item.battle_id}/${item.prediction_time}`} value={itemIndex}>
              {item.prediction_time} · #{item.attacker_number} → #{item.defender_number}
            </option>)}
          </select>
        </label>
        <div className="flex flex-wrap gap-2">
          <button className={buttonClass} disabled={index === 0} onClick={() => { setPlaying(false); setIndex(index - 1); }}>이전 관측</button>
          <button className={buttonClass} disabled={!playing && (Boolean(error) || !visiblePrediction)} onClick={() => setPlaying(!playing)}>{playing ? "일시정지" : "자동 재생"}</button>
          <button className={buttonClass} disabled={index + 1 >= currentPage.items.length} onClick={() => { setPlaying(false); setIndex(index + 1); }}>다음 관측</button>
        </div>
        <p className="text-sm">공격 #{row.attacker_number} → 앞차 #{row.defender_number} · 랩 {row.attacker_lap ?? "—"} · 간격 {row.gap === null ? "—" : `${row.gap.toFixed(3)}초`}</p>
        <p className="break-all text-xs text-zinc-500">관측 시각: {row.prediction_time}</p>
        {predictionLoading && <p role="status" className="text-sm">확률 계산 중…</p>}
        {!error && visiblePrediction && <>
          <ProbabilityGauge value={visiblePrediction.probability} />
          <p className="text-xs text-zinc-400">{visiblePrediction.model} · {visiblePrediction.calibrated ? "보정 확률" : "원본 확률"}</p>
          <p className="text-xs text-zinc-500">{visiblePrediction.data_role === "train" ? "이 경기는 모델 학습에 포함됐습니다. 재생 결과를 독립 평가 성능으로 해석하지 마세요."
            : visiblePrediction.data_role === "calibration" ? "이 경기는 모델 보정용 분할에 포함됐습니다."
            : visiblePrediction.data_role === "test" ? "이 경기는 해당 저장 모델의 평가용 분할입니다." : "이 경기는 저장 모델의 학습·보정 분할에 포함되지 않았습니다."}</p>
        </>}
      </>}
      {currentPage && <div className="flex justify-between gap-2">
        <button className={buttonClass} disabled={pageLoading || offset === 0} onClick={() => { setPlaying(false); setOffset(Math.max(0, offset - 100)); }}>이전 100개</button>
        <button className={buttonClass} disabled={pageLoading || currentPage.next_offset === null} onClick={() => { setPlaying(false); if (currentPage.next_offset !== null) setOffset(currentPage.next_offset); }}>다음 100개</button>
      </div>}
    </section>
  );
}
