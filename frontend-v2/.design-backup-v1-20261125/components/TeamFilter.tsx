import type { CSSProperties } from "react";
import { teamColor } from "@/lib/teams";

type TeamFilterProps = {
  teams: string[];
  selectedTeam: string;
  onSelect: (team: string) => void;
};

function TeamFilter({ teams, selectedTeam, onSelect }: TeamFilterProps) {
  return (
    <div className="chips" role="group" aria-label="팀 필터">
      {teams.map((t) => (
        <button
          key={t}
          type="button"
          className="chip"
          aria-pressed={t === selectedTeam}
          onClick={() => onSelect(t)}
        >
          {t !== "All" && (
            <span
              className="chip-dot"
              style={{ "--team": teamColor(t) } as CSSProperties}
              aria-hidden="true"
            />
          )}
          {t === "All" ? "전체" : t}
        </button>
      ))}
    </div>
  );
}

export default TeamFilter;
