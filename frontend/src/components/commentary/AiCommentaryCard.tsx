import type { AiCommentary } from "@/types/live";

type AiCommentaryCardProps = {
  commentary: AiCommentary | null;
};

export function AiCommentaryCard({ commentary }: AiCommentaryCardProps) {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl backdrop-blur-md">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30 text-xs">
            ✨
          </div>
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-purple-300">
            AI REAL-TIME RACE COMMENTARY
          </h2>
        </div>
        {commentary?.generatedAt && (
          <span className="text-[10px] font-mono text-zinc-500">
            {commentary.generatedAt}
          </span>
        )}
      </div>

      {/* Content */}
      {commentary?.text ? (
        <div className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-4 backdrop-blur-sm">
          <p className="text-sm font-medium leading-relaxed text-zinc-200">
            "{commentary.text}"
          </p>
          <div className="mt-3 flex items-center justify-between text-[10px] text-purple-400/80 font-semibold">
            <span>MODEL: GEMINI REALTIME ANALYTICS</span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-purple-400 animate-ping" /> AUTO-STREAMING
            </span>
          </div>
        </div>
      ) : (
        <div className="flex h-20 items-center justify-center rounded-xl border border-dashed border-white/10 text-xs text-zinc-500">
          Waiting for AI live insight feed...
        </div>
      )}
    </section>
  );
}

