export type Driver = {
  id: number;
  code: string; // 표시용 코드 (VER, NOR 등)
  name: string;
  team: string;
  number: number;
};

// 타이어 정보
export type Tyre = {
  compound: "SOFT" | "MEDIUM" | "HARD";
  age: number; // 사용한 랩 수
};

// 배틀 한 개 (한 관측 시점 기준)
export type Battle = {
  battle_id: string;
  prediction_time: string; // 관측 시각
  lap: number;
  attacker_code: string;   // 공격자 (VER, NOR 등)
  defender_code: string;   // 수비자
  attacker_position: number;
  gap: number;             // 공격자-수비자 간격(초)
  attacker_tyre: Tyre;
  defender_tyre: Tyre;
  probability: number | null; // 3랩 이내 추월 확률(0~1), 계산 불가면 null
};

// 라이브 화면 한 장면
export type LiveState = {
  race_name: string;
  lap: number;
  total_laps: number;
  track_status: "GREEN" | "SC" | "VSC" | "YELLOW";
  battles: Battle[];
  standings: Standing[];
  events: LiveEvent[];
};

//순위표 한 줄
export type Standing={
  position: number;
  code:string;
  gap_ahead:number|null;
  tyre:Tyre;
};

// 최근 이벤트 한 줄
export type LiveEvent = {
  lap: number;
  message: string;
};

// 리플레이 데이터: 장면(LiveState)을 시간 순서대로 모은 것
export type ReplayData = {
  race_name: string;
  frames: LiveState[];
};

