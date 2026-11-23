type TeamFilterProps = {
  teams: string[];
  selectedTeam: string;
  onSelect: (team: string) => void;
};

function TeamFilter({ teams, selectedTeam, onSelect }: TeamFilterProps) {
  return (
    <div className="filters">
      {teams.map((t) => (
        <button
          key={t}
          className={t === selectedTeam ? "active" : ""}
          onClick={() => onSelect(t)}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

export default TeamFilter;