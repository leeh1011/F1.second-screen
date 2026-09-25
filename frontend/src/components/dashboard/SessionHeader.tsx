import { SessionSelector } from "@/components/dashboard/SessionSelector";
import type { OpenF1Session } from "@/lib/api/openf1";
import type { ExtendedLiveSession } from "@/hooks/useOpenF1Session";

type SessionHeaderProps = {
  session: ExtendedLiveSession;
  sessions: OpenF1Session[];
  selectedSessionKey: number | null;
  selectedYear: number;
  onSelectYear: (year: number) => void;
  onSelectSessionKey: (key: number) => void;
  isLoading: boolean;
};

export function SessionHeader({
  session,
  sessions,
  selectedSessionKey,
  selectedYear,
  onSelectYear,
  onSelectSessionKey,
  isLoading,
}: SessionHeaderProps) {
  const isUpcoming = session.isUpcoming;
  const startDate = session.dateStart ? new Date(session.dateStart) : null;
  const formattedDate = startDate
    ? startDate.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
        weekday: "short",
      })
    : "";
  const formattedTime = startDate
    ? startDate.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })
    : "";

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-zinc-950/90 px-6 py-4 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Left: Brand & Session Selector */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-red-500/30 bg-red-500/10 font-extrabold tracking-tighter text-red-500 text-lg shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            F1
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-red-400">
                OPENF1 REAL DATA ANALYTICS
              </p>
            </div>
            <h1 className="text-xl font-extrabold tracking-tight text-white">
              {session.sessionName}
            </h1>
            <p className="text-xs font-medium text-zinc-400">{session.circuitName}</p>
          </div>
        </div>

        {/* Right: Race & Year Selector Control */}
        <div className="flex flex-wrap items-center gap-3">
          <SessionSelector
            sessions={sessions}
            selectedSessionKey={selectedSessionKey}
            selectedYear={selectedYear}
            onSelectYear={onSelectYear}
            onSelectSessionKey={onSelectSessionKey}
            isLoading={isLoading}
          />

          {/* Status Badge */}
          {isUpcoming ? (
            <div className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3.5 py-1.5 text-xs font-bold text-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.2)]">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              <span>UPCOMING ({formattedDate} {formattedTime})</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-bold text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>RECORDED TELEMETRY</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}


