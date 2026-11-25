import type { LiveEvent } from "@/types";

type EventFeedProps = {
  events: LiveEvent[];
};

function EventFeed({ events }: EventFeedProps) {
  if (events.length === 0) {
    return <p className="event-empty">아직 이벤트가 없어요.</p>;
  }
  return (
    <ul className="events">
      {events.map((e, i) => (
        <li key={`${e.lap}-${i}`} className="event">
          <span className="event-lap">{e.lap}랩</span>
          <span>{e.message}</span>
        </li>
      ))}
    </ul>
  );
}

export default EventFeed;
