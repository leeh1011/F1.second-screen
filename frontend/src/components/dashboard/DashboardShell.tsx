"use client";

import { AiCommentaryCard } from "@/components/commentary/AiCommentaryCard";
import { SessionHeader } from "@/components/dashboard/SessionHeader";
import { OvertakePanel } from "@/components/overtake/OvertakePanel";
import { TelemetryPanel } from "@/components/telemetry/TelemetryPanel";
import { TrackMap } from "@/components/track/TrackMap";
import { useOpenF1Session } from "@/hooks/useOpenF1Session";

export function DashboardShell() {
  const {
    sessions,
    selectedSessionKey,
    selectedYear,
    setSelectedYear,
    setSelectedSessionKey,
    sessionData,
    isLoading,
  } = useOpenF1Session();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-red-500 selection:text-white">
      {/* Top Session Header with Race & Year Selector */}
      <SessionHeader
        session={sessionData}
        sessions={sessions}
        selectedSessionKey={selectedSessionKey}
        selectedYear={selectedYear}
        onSelectYear={setSelectedYear}
        onSelectSessionKey={setSelectedSessionKey}
        isLoading={isLoading}
      />

      {/* Main Grid Layout */}
      <main className="mx-auto max-w-7xl grid gap-6 p-6 lg:grid-cols-[1.3fr_1fr]">
        {/* Left Column: Track Map & AI Commentary */}
        <div className="space-y-6">
          <TrackMap
            cars={sessionData.cars}
            circuitName={sessionData.circuitName}
            driversMap={sessionData.driversMap}
            isUpcoming={sessionData.isUpcoming}
          />
          <AiCommentaryCard commentary={sessionData.commentary} />
        </div>

        {/* Right Column: Overtake Battle & Driver Telemetry Leaderboard */}
        <div className="space-y-6">
          <OvertakePanel overtake={sessionData.isUpcoming ? null : sessionData.overtake} />
          <TelemetryPanel
            telemetry={sessionData.telemetry}
            cars={sessionData.cars}
            driversMap={sessionData.driversMap}
            isUpcoming={sessionData.isUpcoming}
          />
        </div>
      </main>
    </div>
  );
}


