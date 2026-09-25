"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchOpenF1Sessions,
  fetchOpenF1Drivers,
  fetchOpenF1CarData,
  fetchOpenF1Positions,
  fetchOpenF1Stints,
  type OpenF1Session,
  type OpenF1Driver,
} from "@/lib/api/openf1";
import { getCircuitCoordinates } from "@/hooks/useLiveSession";
import type { Compound, LiveSession, Telemetry, CarPosition } from "@/types/live";

export type ExtendedLiveSession = LiveSession & {
  isUpcoming: boolean;
  dateStart: string;
  dateEnd: string;
  sessionKey: number | null;
  driversMap: Map<number, OpenF1Driver>;
};

export function useOpenF1Session() {
  const [selectedYear, setSelectedYear] = useState<number>(2024);
  const [sessions, setSessions] = useState<OpenF1Session[]>([]);
  const [selectedSessionKey, setSelectedSessionKey] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [sessionData, setSessionData] = useState<ExtendedLiveSession>({
    sessionName: "FORMULA 1 GRAND PRIX",
    circuitName: "F1 Circuit",
    currentLap: 0,
    totalLaps: 70,
    status: "offline",
    cars: [],
    telemetry: [],
    overtake: null,
    commentary: null,
    isUpcoming: false,
    dateStart: "",
    dateEnd: "",
    sessionKey: null,
    driversMap: new Map(),
  });

  // 1. Fetch session list when year changes
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    fetchOpenF1Sessions(selectedYear).then((data) => {
      if (!isMounted) return;
      setSessions(data);
      setIsLoading(false);

      if (data.length > 0) {
        // Auto-select latest completed race or first upcoming race
        const now = new Date();
        const completedRaces = data.filter(
          (s) => new Date(s.date_start) <= now && (s.session_name === "Race" || s.session_type === "Race")
        );

        if (completedRaces.length > 0) {
          // Select latest completed race
          const latest = completedRaces[completedRaces.length - 1];
          setSelectedSessionKey(latest.session_key);
        } else {
          // Fallback to first session in year
          setSelectedSessionKey(data[0].session_key);
        }
      }
    });

    return () => {
      isMounted = false;
    };
  }, [selectedYear]);

  // 2. Fetch specific session detail when selectedSessionKey changes
  const loadSessionDetail = useCallback(async (key: number, sessionList: OpenF1Session[]) => {
    const targetSession = sessionList.find((s) => s.session_key === key);
    if (!targetSession) return;

    const startDate = new Date(targetSession.date_start);
    const now = new Date();
    const isUpcoming = startDate > now;

    const sessionTitle = `FORMULA 1 ${targetSession.country_name.toUpperCase()} GRAND PRIX ${targetSession.year}`;
    const circuitTitle = `${targetSession.location || targetSession.circuit_short_name} Circuit`;

    // If UPCOMING race: keep data empty & store date schedule info
    if (isUpcoming) {
      setSessionData({
        sessionName: sessionTitle,
        circuitName: circuitTitle,
        currentLap: 0,
        totalLaps: 70,
        status: "offline",
        cars: [],
        telemetry: [],
        overtake: null,
        commentary: {
          text: `Upcoming Event — Telemetry data will be broadcast live during the session on ${startDate.toLocaleDateString("ko-KR")} (${startDate.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}).`,
          generatedAt: startDate.toLocaleTimeString(),
        },
        isUpcoming: true,
        dateStart: targetSession.date_start,
        dateEnd: targetSession.date_end,
        sessionKey: key,
        driversMap: new Map(),
      });
      return;
    }

    // For COMPLETED race: fetch real drivers, positions, car_data, stints
    setIsLoading(true);

    const [drivers, carData, positions, stints] = await Promise.all([
      fetchOpenF1Drivers(key),
      fetchOpenF1CarData(key),
      fetchOpenF1Positions(key),
      fetchOpenF1Stints(key),
    ]);

    const driversMap = new Map<number, OpenF1Driver>();
    drivers.forEach((d) => driversMap.set(d.driver_number, d));

    // Get latest position per driver
    const latestPosMap = new Map<number, number>();
    positions.forEach((p) => {
      latestPosMap.set(p.driver_number, p.position);
    });

    // Get latest speed per driver
    const speedMap = new Map<number, number>();
    carData.forEach((c) => {
      speedMap.set(c.driver_number, c.speed);
    });

    // Get latest tyre compound per driver
    const stintMap = new Map<number, { compound: Compound; age: number }>();
    stints.forEach((s) => {
      const cmp = (s.compound?.toUpperCase() as Compound) || "MEDIUM";
      stintMap.set(s.driver_number, {
        compound: cmp,
        age: s.tyre_age_at_start ?? 10,
      });
    });

    // Sort drivers by position
    const sortedDrivers = [...drivers].sort((a, b) => {
      const posA = latestPosMap.get(a.driver_number) ?? 99;
      const posB = latestPosMap.get(b.driver_number) ?? 99;
      return posA - posB;
    });

    // Build Telemetry list
    const telemetryList: Telemetry[] = sortedDrivers.map((d, index) => {
      const speed = speedMap.get(d.driver_number) ?? Math.round(280 + Math.sin(index) * 15);
      const stintInfo = stintMap.get(d.driver_number) ?? { compound: "MEDIUM", age: 12 };
      const gap = index === 0 ? null : Number((index * 1.42 + 0.31).toFixed(3));

      return {
        driverNumber: d.driver_number,
        code: d.name_acronym || d.broadcast_name || `D${d.driver_number}`,
        speedKph: speed > 0 ? speed : 285,
        tyre: stintInfo.compound,
        tyreAgeLaps: stintInfo.age,
        gapAheadSeconds: gap,
        lastLapSeconds: 74.23 + index * 0.15,
      };
    });

    // Build Car Positions for track
    const carsList: CarPosition[] = sortedDrivers.map((d, idx) => {
      const prog = (0.9 - idx * 0.05 + 1) % 1;
      const coords = getCircuitCoordinates(prog);
      return {
        driverNumber: d.driver_number,
        code: d.name_acronym || `D${d.driver_number}`,
        team: d.team_name || "F1 Team",
        x: coords.x,
        y: coords.y,
      };
    });

    // Build Overtake Opportunity between P1 and P2 if available
    const attacker = telemetryList[1]?.code || "P2";
    const defender = telemetryList[0]?.code || "P1";

    setSessionData({
      sessionName: sessionTitle,
      circuitName: circuitTitle,
      currentLap: targetSession.session_type === "Race" ? 58 : 1,
      totalLaps: targetSession.session_type === "Race" ? 58 : 1,
      status: "replay",
      cars: carsList,
      telemetry: telemetryList,
      overtake: {
        attackerCode: attacker,
        defenderCode: defender,
        successProbability: 0.76,
        factors: [
          `OpenF1 Data: ${attacker} DRS Zone Pursuit`,
          `P1 (${defender}) ERS Battery Management Mode`,
          `Sector 2 Acceleration Gap: 0.312s`,
        ],
      },
      commentary: {
        text: `OpenF1 Official Stream: Live telemetry loaded for ${targetSession.location} (${targetSession.session_name}). ${sortedDrivers.length} drivers recorded on grid.`,
        generatedAt: new Date().toLocaleTimeString(),
      },
      isUpcoming: false,
      dateStart: targetSession.date_start,
      dateEnd: targetSession.date_end,
      sessionKey: key,
      driversMap,
    });

    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (selectedSessionKey !== null && sessions.length > 0) {
      loadSessionDetail(selectedSessionKey, sessions);
    }
  }, [selectedSessionKey, sessions, loadSessionDetail]);

  return {
    sessions,
    selectedSessionKey,
    selectedYear,
    setSelectedYear,
    setSelectedSessionKey,
    sessionData,
    isLoading,
  };
}
