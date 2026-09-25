import { DriverTelemetryCard } from "@/components/telemetry/DriverTelemetryCard";
import type { OpenF1Driver } from "@/lib/api/openf1";
import type { CarPosition, Telemetry } from "@/types/live";

type TelemetryPanelProps = {
  telemetry: Telemetry[];
  cars: CarPosition[];
  driversMap?: Map<number, OpenF1Driver>;
  isUpcoming?: boolean;
};

export function TelemetryPanel({ telemetry, cars, driversMap, isUpcoming }: TelemetryPanelProps) {
  // Map driver code to team name
  const teamMap = new Map<string, string>();
  cars.forEach((c) => teamMap.set(c.code, c.team));

  if (isUpcoming || telemetry.length === 0) {
    return (
      <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
        <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-300">
              TELEMETRY LEADERBOARD
            </h2>
          </div>
          <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
            UPCOMING RACE
          </span>
        </div>

        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/10 bg-zinc-950/50 py-12 px-4 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xl font-bold">
            🏎️
          </div>
          <h3 className="text-sm font-bold text-zinc-200">Session Has Not Started Yet</h3>
          <p className="mt-1 text-xs text-zinc-500 max-w-sm">
            Telemetry data (live speeds, tyre stints, sector gaps, and leaderboards) will be captured and displayed when the session goes live.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
      <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-300">
            DRIVER TELEMETRY LEADERBOARD
          </h2>
        </div>
        <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
          {telemetry.length} DRIVERS RECORDED
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {telemetry.map((item, idx) => {
          const openf1Driver = driversMap?.get(item.driverNumber);
          return (
            <DriverTelemetryCard
              key={item.driverNumber}
              telemetry={item}
              position={idx + 1}
              teamName={openf1Driver?.team_name || teamMap.get(item.code) || "F1 Team"}
              headshotUrl={openf1Driver?.headshot_url}
            />
          );
        })}
      </div>
    </section>
  );
}


