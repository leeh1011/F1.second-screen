export type OpenF1Session = {
  session_key: number;
  session_name: string;
  session_type: string;
  date_start: string;
  date_end: string;
  meeting_key: number;
  circuit_key: number;
  circuit_short_name: string;
  country_name: string;
  country_code: string;
  location: string;
  year: number;
  is_cancelled?: boolean;
};

export type OpenF1Driver = {
  session_key: number;
  driver_number: number;
  broadcast_name: string;
  full_name: string;
  name_acronym: string;
  team_name: string;
  team_colour: string;
  headshot_url: string | null;
  country_code: string;
};

export type OpenF1CarData = {
  driver_number: number;
  speed: number;
  rpm: number;
  gear: number;
  throttle: number;
  brake: number;
  drs: number;
  date: string;
};

export type OpenF1Position = {
  driver_number: number;
  position: number;
  date: string;
};

export type OpenF1Stint = {
  driver_number: number;
  compound: string;
  tyre_age_at_start: number;
  stint_number: number;
};

const OPENF1_BASE_URL = "https://api.openf1.org/v1";

export async function fetchOpenF1Sessions(year = 2024): Promise<OpenF1Session[]> {
  try {
    const res = await fetch(`${OPENF1_BASE_URL}/sessions?year=${year}`);
    if (!res.ok) throw new Error(`OpenF1 HTTP error: ${res.status}`);
    const data: OpenF1Session[] = await res.json();

    // Sort chronologically
    return data.sort(
      (a, b) => new Date(a.date_start).getTime() - new Date(b.date_start).getTime()
    );
  } catch (err) {
    console.error("Failed to fetch OpenF1 sessions:", err);
    return [];
  }
}

export async function fetchOpenF1Drivers(sessionKey: number): Promise<OpenF1Driver[]> {
  try {
    const res = await fetch(`${OPENF1_BASE_URL}/drivers?session_key=${sessionKey}`);
    if (!res.ok) throw new Error(`OpenF1 HTTP error: ${res.status}`);
    const data: OpenF1Driver[] = await res.json();
    return data;
  } catch (err) {
    console.error(`Failed to fetch drivers for session ${sessionKey}:`, err);
    return [];
  }
}

export async function fetchOpenF1CarData(sessionKey: number): Promise<OpenF1CarData[]> {
  try {
    // Fetch latest car speed/telemetry sample
    const res = await fetch(`${OPENF1_BASE_URL}/car_data?session_key=${sessionKey}`);
    if (!res.ok) return [];
    const data: OpenF1CarData[] = await res.json();
    return data;
  } catch (err) {
    console.error(`Failed to fetch car_data for session ${sessionKey}:`, err);
    return [];
  }
}

export async function fetchOpenF1Positions(sessionKey: number): Promise<OpenF1Position[]> {
  try {
    const res = await fetch(`${OPENF1_BASE_URL}/position?session_key=${sessionKey}`);
    if (!res.ok) return [];
    const data: OpenF1Position[] = await res.json();
    return data;
  } catch (err) {
    console.error(`Failed to fetch position for session ${sessionKey}:`, err);
    return [];
  }
}

export async function fetchOpenF1Stints(sessionKey: number): Promise<OpenF1Stint[]> {
  try {
    const res = await fetch(`${OPENF1_BASE_URL}/stints?session_key=${sessionKey}`);
    if (!res.ok) return [];
    const data: OpenF1Stint[] = await res.json();
    return data;
  } catch (err) {
    console.error(`Failed to fetch stints for session ${sessionKey}:`, err);
    return [];
  }
}
