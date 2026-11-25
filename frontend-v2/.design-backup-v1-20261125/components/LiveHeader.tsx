import type { LiveState } from "@/types";

type LiveHeaderProps = {
  liveState: LiveState;
};

const STATUS_LABEL: Record<LiveState["track_status"], string> = {
  GREEN: "정상 주행",
  YELLOW: "옐로 플래그",
  SC: "세이프티카",
  VSC: "가상 세이프티카",
};

function LiveHeader({ liveState }: LiveHeaderProps) {
  const { race_name, lap, total_laps, track_status } = liveState;
  const progress = Math.min(100, Math.round((lap / total_laps) * 100));

  return (
    <div className="race-strip">
      <div className="race-top">
        <h1 className="race-name">{race_name}</h1>
        <span className={`flag flag-${track_status.toLowerCase()}`}>
          {STATUS_LABEL[track_status]}
        </span>
      </div>
      <div className="lap-line">
        <span className="lap-now">{lap}</span>
        <span className="lap-total">/ {total_laps}랩</span>
        <div
          className="lap-bar"
          role="progressbar"
          aria-label="레이스 진행"
          aria-valuemin={0}
          aria-valuemax={total_laps}
          aria-valuenow={lap}
        >
          <span className="lap-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
}

export default LiveHeader;
