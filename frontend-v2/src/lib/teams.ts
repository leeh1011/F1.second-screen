// 팀 대표색 (드라이버 번호·필터 점에만 사용). 목록에 없는 팀은 회색.
const TEAM_COLORS: Record<string, string> = {
  Mercedes: "#27f4d2",
  Ferrari: "#ff5a4f",
  "Red Bull": "#5b8fe0",
  McLaren: "#ff8000",
};

export function teamColor(team: string): string {
  return TEAM_COLORS[team] ?? "#9aa5b0";
}
