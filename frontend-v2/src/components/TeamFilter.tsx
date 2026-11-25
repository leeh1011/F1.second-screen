import type { CSSProperties } from "react";
import { themeFor } from "@/lib/teams";

type TeamFilterProps = {
  teams: string[];
  selectedTeam: string;
  onSelect: (team: string) => void;
};

function TeamFilter({ teams, selectedTeam, onSelect }: TeamFilterProps) {
  return (
    <div className="chips" role="group" aria-label="팀 필터">
      {teams.map((t) => {
        const theme = t === "All" ? null : themeFor(t);
        const style = theme
          ? ({ "--team": theme.accent, "--on-team": theme.on } as CSSProperties)
          : undefined;
        return (
          <button
            key={t}
            type="button"
            className="chip"
            style={style}
            aria-pressed={t === selectedTeam}
            onClick={() => onSelect(t)}
          >
            {theme && <span className="chip-dot" aria-hidden="true" />}
            {t === "All" ? "전체" : t}
          </button>
        );
      })}
    </div>
  );
}

export default TeamFilter;
