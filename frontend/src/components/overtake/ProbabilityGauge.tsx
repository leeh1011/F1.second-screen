type ProbabilityGaugeProps = {
  value: number;
};

export function ProbabilityGauge({ value }: ProbabilityGaugeProps) {
  const percent = Math.min(100, Math.max(0, Math.round(value * 100)));

  const getGradient = (pct: number) => {
    if (pct >= 70) return "from-emerald-500 to-teal-400 shadow-[0_0_12px_rgba(16,185,129,0.4)]";
    if (pct >= 40) return "from-amber-500 to-yellow-400 shadow-[0_0_12px_rgba(245,158,11,0.4)]";
    return "from-red-600 to-rose-500 shadow-[0_0_12px_rgba(225,29,72,0.4)]";
  };

  const getTextColor = (pct: number) => {
    if (pct >= 70) return "text-emerald-400";
    if (pct >= 40) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
          OVERTAKE PREDICTION
        </span>
        <div className="flex items-baseline gap-1">
          <span className={`text-3xl font-extrabold tracking-tight ${getTextColor(percent)}`}>
            {percent}
          </span>
          <span className="text-sm font-bold text-zinc-400">%</span>
        </div>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-zinc-950 p-0.5 border border-white/10 shadow-inner">
        <div
          className={`h-full rounded-full bg-gradient-to-r transition-all duration-300 ease-out ${getGradient(percent)}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

