export type SessionStatus = "live" | "replay" | "offline";

export type Compound = "SOFT" | "MEDIUM" | "HARD" | "INTERMEDIATE" | "WET";

export type CarPosition = {
  driverNumber: number;
  code: string;
  team: string;
  x: number;
  y: number;
};

export type Telemetry = {
  driverNumber: number;
  code: string;
  speedKph: number;
  tyre: Compound;
  tyreAgeLaps: number;
  gapAheadSeconds: number | null;
  lastLapSeconds: number | null;
};

export type OvertakeOpportunity = {
  attackerCode: string;
  defenderCode: string;
  successProbability: number;
  factors: string[];
};

export type AiCommentary = {
  text: string;
  generatedAt: string;
};

export type LiveSession = {
  sessionName: string;
  circuitName: string;
  currentLap: number;
  totalLaps: number;
  status: SessionStatus;
  cars: CarPosition[];
  telemetry: Telemetry[];
  overtake: OvertakeOpportunity | null;
  commentary: AiCommentary | null;
};
