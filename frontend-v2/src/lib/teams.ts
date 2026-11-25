// 팀 색과 드라이버→팀 매핑.
// 화면 전체의 강조색(--accent)이 여기서 나온다: 선두 팀 색 = 페이지 테마, 추격차 팀 색 = 배틀 카드.

export type Theme = {
  accent: string; // 강조색 (어두운 배경에서 잘 보이게 공식 색을 밝기 조정한 값)
  on: string;     // 강조색 위에 올리는 글자색
};

const THEMES: Record<string, Theme> = {
  "Red Bull": { accent: "#4f8cff", on: "#0a1020" },
  Ferrari: { accent: "#ff4a3d", on: "#1a0705" },
  Mercedes: { accent: "#27f4d2", on: "#04201c" },
  McLaren: { accent: "#ff8000", on: "#1f0f00" },
  "Aston Martin": { accent: "#34c38f", on: "#04180f" },
  Alpine: { accent: "#ff7fc0", on: "#240614" },
  Williams: { accent: "#5ac8fa", on: "#04141c" },
  RB: { accent: "#8fa8ff", on: "#0a1030" },
  "Kick Sauber": { accent: "#5ee05e", on: "#051805" },
  Haas: { accent: "#eceef1", on: "#1b1f24" },
};

// 팀을 모르거나 팀 화면이 아닐 때의 중립색
export const NEUTRAL_THEME: Theme = { accent: "#e6e9ec", on: "#1b1f24" };

export function themeFor(team?: string | null): Theme {
  return (team && THEMES[team]) || NEUTRAL_THEME;
}

// 드라이버 번호·필터 점 등에 쓰는 팀 색
export function teamColor(team: string): string {
  return themeFor(team).accent;
}

// 시즌별 그리드. 같은 코드도 시즌에 따라 팀이 달라진다. (예: HAM 2024 Mercedes, 2026 Ferrari)
// 나중에는 API가 드라이버마다 team을 내려주는 쪽이 정확하다.
const GRID: Record<number, Record<string, string>> = {
  2024: {
    VER: "Red Bull", PER: "Red Bull",
    LEC: "Ferrari", SAI: "Ferrari",
    HAM: "Mercedes", RUS: "Mercedes",
    NOR: "McLaren", PIA: "McLaren",
    ALO: "Aston Martin", STR: "Aston Martin",
    GAS: "Alpine", OCO: "Alpine",
    ALB: "Williams", SAR: "Williams",
    TSU: "RB", RIC: "RB",
    BOT: "Kick Sauber", ZHO: "Kick Sauber",
    MAG: "Haas", HUL: "Haas",
  },
  2026: {
    ANT: "Mercedes", RUS: "Mercedes",
    HAM: "Ferrari", LEC: "Ferrari",
    VER: "Red Bull",
    NOR: "McLaren", PIA: "McLaren",
  },
};

// "2024 바레인 GP" → 2024
export function seasonOf(raceName: string): number | undefined {
  const m = /^(\d{4})/.exec(raceName);
  return m ? Number(m[1]) : undefined;
}

export function teamOfDriver(code: string, season?: number): string | undefined {
  if (season && GRID[season]?.[code]) return GRID[season][code];
  // 시즌을 모르면 최신 시즌부터 찾는다
  const years = Object.keys(GRID).map(Number).sort((a, b) => b - a);
  for (const y of years) {
    if (GRID[y][code]) return GRID[y][code];
  }
  return undefined;
}
