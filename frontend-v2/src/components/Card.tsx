import type { CSSProperties } from "react";
import { teamColor } from "@/lib/teams";

type CardProps = {
  name: string;
  team: string;
  number: number;
  code?: string;
};

function Card({ name, team, number, code }: CardProps) {
  return (
    <div className="driver-row" style={{ "--team": teamColor(team) } as CSSProperties}>
      <span className="driver-number">{number}</span>
      <div>
        <h2 className="driver-name">{name}</h2>
        <p className="driver-team">{team}</p>
      </div>
      {code && <span className="driver-code">{code}</span>}
    </div>
  );
}

export default Card;
