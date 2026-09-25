import type { CarPosition } from "@/types/live";
import { getTeamHex } from "@/lib/teamColors";

type CarMarkerProps = {
  car: CarPosition;
  index: number;
  teamColour?: string;
};

export function CarMarker({ car, index, teamColour }: CarMarkerProps) {
  const teamHex = getTeamHex(teamColour || car.team);
  const px = car.x * 1000;
  const py = car.y * 520;


  return (
    <g transform={`translate(${px}, ${py})`} className="transition-transform duration-150 ease-out">
      {/* Outer Pulse Glow */}
      <circle r="16" fill={teamHex} opacity="0.25" className="animate-pulse" />

      {/* Main Car Dot */}
      <circle r="10" fill="#09090b" stroke={teamHex} strokeWidth="3" className="shadow-lg" />

      {/* Driver Position Rank Number inside Dot */}
      <text
        y="3.5"
        textAnchor="middle"
        fill="#ffffff"
        fontSize="9"
        fontWeight="800"
        fontFamily="sans-serif"
      >
        {index + 1}
      </text>

      {/* Driver Code Pill Label above Dot */}
      <g transform="translate(0, -18)">
        <rect
          x="-18"
          y="-9"
          width="36"
          height="14"
          rx="4"
          fill="#18181b"
          stroke={teamHex}
          strokeWidth="1.2"
          opacity="0.9"
        />
        <text
          y="1"
          textAnchor="middle"
          fill="#ffffff"
          fontSize="9"
          fontWeight="700"
          fontFamily="sans-serif"
          letterSpacing="0.5"
        >
          {car.code}
        </text>
      </g>
    </g>
  );
}

