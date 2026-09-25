import { env } from "@/lib/env";
import type { LiveSession } from "@/types/live";

export async function fetchLiveSession(): Promise<LiveSession> {
  const response = await fetch(`${env.apiUrl}/api/session/live`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch live session: ${response.status}`);
  }

  return response.json();
}
