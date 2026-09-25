import type { Telemetry } from "@/types/live";
import { COMPOUND_COLORS, getTeamHex } from "@/lib/teamColors";

type DriverTelemetryCardProps = {
  telemetry: Telemetry;
  position: number;
  teamName?: string;
  headshotUrl?: string | null;
};

export function DriverTelemetryCard({
  telemetry,
  position,
  teamName = "F1 Team",
  headshotUrl,
}: DriverTelemetryCardProps) {
  const teamHex = getTeamHex(teamName);
  const compoundStyle = COMPOUND_COLORS[telemetry.tyre] ?? COMPOUND_COLORS["HARD"];

  // Speed bar percentage relative to 350 kph
  const speedPct = Math.min(100, Math.max(10, Math.round((telemetry.speedKph / 350) * 100)));

  return (
    <article className="group relative overflow-hidden rounded-xl border border-white/10 bg-zinc-950/70 p-3.5 transition-all duration-200 hover:border-white/20 hover:bg-zinc-900/90 shadow-lg">
      {/* Team Color Left Border Strip */}
      <div
        className="absolute left-0 top-0 bottom-0 w-1"
        style={{ backgroundColor: teamHex }}
      />

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-800 text-xs font-black text-white border border-white/10">
            P{position}
          </span>

          {/* Driver Headshot Avatar */}
          {headshotUrl ? (
            <img
              src={headshotUrl}
              alt={telemetry.code}
              className="h-8 w-8 rounded-full border border-white/10 bg-zinc-800 object-cover object-top shadow-sm"
              onError={(e) => {
                // Hide broken images cleanly
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          ) : (
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
              style={{ backgroundColor: `${teamHex}40`, border: `1px solid ${teamHex}` }}
            >
              {telemetry.code.slice(0, 2)}
            </div>
          )}

          <div>
            <h3 className="text-sm font-black tracking-tight text-white group-hover:text-amber-400 transition-colors">
              {telemetry.code}
            </h3>
            <p className="text-[10px] text-zinc-500 font-semibold">{teamName}</p>
          </div>
        </div>

        {/* Tyre Compound Badge */}
        <div className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-bold ${compoundStyle.bg} ${compoundStyle.text} ${compoundStyle.border}`}>
          <span>{telemetry.tyre}</span>
          <span className="opacity-60">L{telemetry.tyreAgeLaps}</span>
        </div>
      </div>

      {/* Speed & Gap Metrics */}
      <div className="mt-3 flex items-baseline justify-between">
        <div className="flex items-baseline gap-1">
          <span className="text-xl font-black text-white tracking-tight">{telemetry.speedKph}</span>
          <span className="text-[10px] font-bold text-zinc-400">km/h</span>
        </div>

        <div className="text-right text-[11px] font-medium text-zinc-400">
          {telemetry.gapAheadSeconds !== null ? (
            <span className="text-amber-400 font-semibold">+{telemetry.gapAheadSeconds}s</span>
          ) : (
            <span className="text-emerald-400 font-bold uppercase tracking-wider">LEADER</span>
          )}
        </div>
      </div>

      {/* Dynamic Speed Bar */}
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-900">
        <div
          className="h-full rounded-full transition-all duration-200"
          style={{ width: `${speedPct}%`, backgroundColor: teamHex }}
        />
      </div>

      {/* Last Lap Time */}
      {telemetry.lastLapSeconds && (
        <p className="mt-1.5 text-[10px] text-zinc-500 font-mono text-right">
          LAST: {telemetry.lastLapSeconds.toFixed(3)}s
        </p>
      )}
    </article>
  );
}


