"use client";

import { useMemo } from "react";
import type { OpenF1Session } from "@/lib/api/openf1";

type SessionSelectorProps = {
  sessions: OpenF1Session[];
  selectedSessionKey: number | null;
  selectedYear: number;
  onSelectYear: (year: number) => void;
  onSelectSessionKey: (key: number) => void;
  isLoading: boolean;
};

export function SessionSelector({
  sessions,
  selectedSessionKey,
  selectedYear,
  onSelectYear,
  onSelectSessionKey,
  isLoading,
}: SessionSelectorProps) {
  const now = new Date();

  // Categorize sessions into Races vs All
  const raceSessions = useMemo(() => {
    // Filter only Races or Sprints for primary dropdown, fallback to all if empty
    const races = sessions.filter(
      (s) => s.session_name === "Race" || s.session_name === "Sprint" || s.session_type === "Race"
    );
    return races.length > 0 ? races : sessions;
  }, [sessions]);

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Year Selector */}
      <div className="flex items-center rounded-xl border border-white/10 bg-zinc-900/90 p-1 backdrop-blur-md shadow-inner">
        {[2024, 2025, 2026].map((yr) => (
          <button
            key={yr}
            onClick={() => onSelectYear(yr)}
            className={`rounded-lg px-3 py-1 text-xs font-extrabold transition-all ${
              selectedYear === yr
                ? "bg-red-600 text-white shadow-[0_0_10px_rgba(225,29,72,0.4)]"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            }`}
          >
            {yr}
          </button>
        ))}
      </div>

      {/* Race / Session Dropdown */}
      <div className="relative min-w-[260px] sm:min-w-[320px]">
        <select
          value={selectedSessionKey ?? ""}
          onChange={(e) => onSelectSessionKey(Number(e.target.value))}
          disabled={isLoading || sessions.length === 0}
          className="w-full appearance-none rounded-xl border border-white/15 bg-zinc-900/90 py-2 pl-3.5 pr-10 text-xs font-bold text-white shadow-lg backdrop-blur-md transition-all focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:opacity-50 cursor-pointer"
        >
          {sessions.length === 0 && (
            <option value="">{isLoading ? "Loading F1 Sessions..." : "No sessions found"}</option>
          )}

          {raceSessions.map((s) => {
            const startDate = new Date(s.date_start);
            const isUpcoming = startDate > now;
            const dateStr = startDate.toLocaleDateString("ko-KR", {
              month: "short",
              day: "numeric",
            });
            const statusLabel = isUpcoming ? `[Upcoming ${dateStr}]` : `[Finished ${dateStr}]`;

            return (
              <option key={s.session_key} value={s.session_key}>
                {statusLabel} {s.location || s.country_name} — {s.session_name} ({s.circuit_short_name})
              </option>
            );
          })}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-zinc-400">
          <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
    </div>
  );
}
