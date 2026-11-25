type ReplayControlsProps = {
  playing: boolean;
  frameIndex: number;
  totalFrames: number;
  onTogglePlay: () => void; // 재생/일시정지 눌렀을 때
  onReset: () => void;      // 처음으로 눌렀을 때
};

function ReplayControls({
  playing, frameIndex, totalFrames, onTogglePlay, onReset,
}: ReplayControlsProps) {
  const atEnd = frameIndex === totalFrames - 1; // 마지막 장면 확인

  return (
    <div className="replay" role="group" aria-label="리플레이 컨트롤">
      <button className="replay-play" onClick={onTogglePlay} disabled={atEnd}>
        {playing && !atEnd ? "일시정지" : "재생"}
      </button>
      <div className="replay-steps" aria-hidden="true">
        {Array.from({ length: totalFrames }, (_, i) => (
          <span
            key={i}
            className={`replay-step${i <= frameIndex ? " replay-step-on" : ""}`}
          />
        ))}
      </div>
      <span className="replay-count">{frameIndex + 1}/{totalFrames}</span>
      <button className="replay-reset" onClick={onReset}>처음으로</button>
    </div>
  );
}

export default ReplayControls;
