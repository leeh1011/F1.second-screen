import { env } from "@/lib/env";
import type { LiveSession } from "@/types/live";

type MessageHandler = (session: LiveSession) => void;

export function connectLiveSocket(onMessage: MessageHandler) {
  const socket = new WebSocket(env.wsUrl);

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data) as LiveSession;
    onMessage(payload);
  };

  return {
    close: () => socket.close(),
  };
}
