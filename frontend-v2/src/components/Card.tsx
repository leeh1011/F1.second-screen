import type { CSSProperties } from "react";
import { themeFor } from "@/lib/teams";

type CardProps = {
  name: string;
  team: string;
  number: number;
  code?: string;
};

function Card({ name, team, number, code }: CardProps) {
  const theme = themeFor(team);
  return (
    <div
      className="driver-row"
      style={{ "--team": theme.accent, "--on-team": theme.on } as CSSProperties}
    >
      <span className="driver-number">{number}</span>
      <div>
        <h2 className="driver-name">{name}</h2>
        <p className="driver-team">{team}</p>
      </div>
      {code && <span className="driver-tag">{code}</span>}
    </div>
  );
}

export default Card;
