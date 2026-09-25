"use client";

import { useEffect, useState } from "react";
import { connectLiveSocket } from "@/lib/api/websocket";
import { env } from "@/lib/env";
import { mockLiveSession } from "@/mocks/live-session";
import type { LiveSession } from "@/types/live";

// Realistic parametric circuit path mapping
export function getCircuitCoordinates(progress: number): { x: number; y: number } {
  const t = (progress % 1) * 2 * Math.PI;
  // Smooth organic track shape
  const scaleX = 0.38;
  const scaleY = 0.28;
  const r = 1 + 0.18 * Math.sin(3 * t) - 0.12 * Math.cos(2 * t);
  const x = 0.5 + r * scaleX * Math.cos(t);
  const y = 0.5 + r * scaleY * Math.sin(t);
  return {
    x: Number(Math.max(0.08, Math.min(0.92, x)).toFixed(4)),
    y: Number(Math.max(0.1, Math.min(0.9, y)).toFixed(4)),
  };
}

export function useLiveSession() {
  const [session, setSession] = useState<LiveSession>(mockLiveSession);
  const [usingMock] = useState(env.useMock);

  useEffect(() => {
    if (!usingMock) {
      const connection = connectLiveSocket(setSession);
      return () => connection.close();
    }

    // Dynamic Live Simulation for Mock Mode
    let frame = 0;
    const initialProgresses = [0.85, 0.83, 0.77, 0.72, 0.65, 0.58, 0.49, 0.42];

    const interval = setInterval(() => {
      frame += 1;
      const timeOffset = frame * 0.003;

      setSession((prev) => {
        const updatedCars = prev.cars.map((car, idx) => {
          const prog = (initialProgresses[idx] + timeOffset) % 1;
          const coords = getCircuitCoordinates(prog);
          return { ...car, x: coords.x, y: coords.y };
        });

        const updatedTelemetry = prev.telemetry.map((t, idx) => {
          const speedVariance = Math.round(Math.sin(frame * 0.2 + idx) * 8);
          const baseSpeed = idx === 0 ? 302 : 295 - idx * 2;
          return {
            ...t,
            speedKph: Math.min(335, Math.max(260, baseSpeed + speedVariance)),
          };
        });

        // Dynamic overtake calculation fluctuation
        const probability = Number(
          (0.75 + 0.15 * Math.sin(frame * 0.1)).toFixed(2)
        );

        return {
          ...prev,
          cars: updatedCars,
          telemetry: updatedTelemetry,
          overtake: prev.overtake
            ? { ...prev.overtake, successProbability: probability }
            : null,
        };
      });
    }, 150);

    return () => clearInterval(interval);
  }, [usingMock]);

  return { session, usingMock };
}

