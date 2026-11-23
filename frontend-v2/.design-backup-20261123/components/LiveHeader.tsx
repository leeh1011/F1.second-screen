import type { LiveState } from "@/types";

type LiveHeaderProps = {
  liveState: LiveState;
};

function LiveHeader({ liveState }: LiveHeaderProps) {
  const { race_name, lap, total_laps, track_status } = liveState;

  return (
    <div className="live-header">
      <h2>{race_name}</h2>
      <div className="live-header-info">
        <span className="live-header-lap">
          LAP {lap} / {total_laps}
        </span>
        <span className={`live-header-status status-${track_status.toLowerCase()}`}>
          {track_status}
        </span>
      </div>
    </div>
  );
}

export default LiveHeader;