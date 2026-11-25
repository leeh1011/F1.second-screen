import { env } from "@/lib/env";

export type BattleObservation = {
  battle_id: string;
  prediction_time: string;
  attacker_number: number;
  defender_number: number;
  attacker_lap: number | null;
  gap: number | null;
  battle_ready: boolean;
};

export type BattlePage = {
  items: BattleObservation[];
  total: number;
  next_offset: number | null;
};

export type ReplayPrediction = {
  probability: number;
  model: string;
  variant: string;
  calibrated: boolean;
  data_role: string;
};

async function request<T>(path: string, options: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${env.apiUrl.replace(/\/$/, "")}${path}`, { cache: "no-store", ...options });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error("예측 서버에 연결할 수 없습니다. 백엔드 실행과 API 주소를 확인해 주세요.");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const fallback = response.status === 503 ? "학습 모델이 준비되지 않았습니다."
      : response.status === 404 ? "이 경기의 저장된 배틀 데이터가 없습니다."
      : response.status === 422 ? "이 관측은 예측에 필요한 조건을 충족하지 않습니다."
      : "예측 요청 처리에 실패했습니다.";
    throw new Error(typeof body?.detail === "string" ? body.detail : fallback);
  }
  if (body === null) throw new Error("서버 응답을 읽을 수 없습니다.");
  return body as T;
}

export async function fetchBattles(session: number, offset: number, signal: AbortSignal): Promise<BattlePage> {
  const page = await request<BattlePage>(`/api/races/${session}/battles?ready_only=true&limit=100&offset=${offset}`, { signal });
  if (!Array.isArray(page.items) || !Number.isInteger(page.total) || page.total < 0
      || (page.next_offset !== null && (!Number.isInteger(page.next_offset) || page.next_offset <= offset))) {
    throw new Error("저장 관측 목록 형식이 올바르지 않습니다.");
  }
  return page;
}

export async function fetchPrediction(row: BattleObservation, signal: AbortSignal): Promise<ReplayPrediction> {
  const result = await request<ReplayPrediction>("/api/prediction/overtake", {
    method: "POST", signal, headers: { "Content-Type": "application/json" },
    // Preserve the original timestamp including microseconds; JS Date would truncate it.
    body: JSON.stringify({ battle_id: row.battle_id, prediction_time: row.prediction_time }),
  });
  if (!Number.isFinite(result.probability) || result.probability < 0 || result.probability > 1) {
    throw new Error("서버가 유효하지 않은 확률을 반환했습니다.");
  }
  return result;
}
