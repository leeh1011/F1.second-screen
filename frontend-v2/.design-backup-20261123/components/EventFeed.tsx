import type { LiveEvent } from "@/types";

type EventFeedProps={
    events:LiveEvent[];
};

function EventFeed({events}:EventFeedProps){
    if(events.length===0){
        return <p className="event-empty">아직 이벤트가 없어요.</p>;
    }
    return (
    <ul className="event-feed">
      {events.map((e, i) => (
        <li key={i}>
          <span className="event-lap">L{e.lap}</span>
          <span className="event-message">{e.message}</span>
        </li>
      ))}
    </ul>
  );
}

export default EventFeed;