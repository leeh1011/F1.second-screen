import { ProbabilityGauge } from "@/components/overtake/ProbabilityGauge";
import type { OvertakeOpportunity } from "@/types/live";

type OvertakePanelProps = {
  overtake: OvertakeOpportunity | null;
};

export function OvertakePanel({ overtake }: OvertakePanelProps) {
  if (!overtake) {
    return (
      <section className="rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
        <h2 className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-zinc-400">
          REAL-TIME OVERTAKE BATTLE
        </h2>
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-white/10 bg-zinc-950/50 text-xs text-zinc-500">
          No high-probability overtake opportunity detected
        </div>
      </section>
    );
  }

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
      {/* Top Banner */}
      <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
          </span>
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-amber-400">
            LIVE OVERTAKE BATTLE
          </h2>
        </div>
        <span className="rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/20 uppercase">
          HOT ZONE
        </span>
      </div>

      {/* Attacker vs Defender */}
      <div className="mb-5 flex items-center justify-between rounded-xl border border-white/10 bg-zinc-950/80 p-4 shadow-inner">
        <div className="text-center">
          <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400">ATTACKER</p>
          <p className="mt-1 text-2xl font-black text-white">{overtake.attackerCode}</p>
        </div>

        <div className="flex flex-col items-center">
          <span className="rounded-full bg-red-600/20 px-3 py-1 text-xs font-black text-red-500 border border-red-500/30">
            VS
          </span>
        </div>

        <div className="text-center">
          <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">DEFENDER</p>
          <p className="mt-1 text-2xl font-black text-zinc-300">{overtake.defenderCode}</p>
        </div>
      </div>

      {/* Gauge */}
      <div className="mb-5">
        <ProbabilityGauge value={overtake.successProbability} />
      </div>

      {/* Advantage Factors */}
      <div>
        <h3 className="mb-2 text-[11px] font-bold uppercase tracking-wider text-zinc-400">
          KEY ADVANTAGE FACTORS
        </h3>
        <ul className="space-y-1.5">
          {overtake.factors.map((factor, idx) => (
            <li
              key={idx}
              className="flex items-center gap-2 rounded-lg border border-white/5 bg-zinc-950/40 px-3 py-1.5 text-xs text-zinc-300"
            >
              <span className="text-emerald-400 text-sm">✓</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

