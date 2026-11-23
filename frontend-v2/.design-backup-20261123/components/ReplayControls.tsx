type ReplayControlsProps={
    playing:boolean;
    frameIndex:number;
    totalFrames:number;
    onTogglePlay:()=>void;  // 재생/일시정지 눌렀을 때
    onReset:()=>void;       //처음으로 눌렀을 때
};

function ReplayControls({
  playing, frameIndex, totalFrames, onTogglePlay, onReset,
}: ReplayControlsProps){
    const atEnd=frameIndex===totalFrames-1; //마지막 장명확인

    return (
        <div className="replay-controls">
            <button onClick={onTogglePlay} disabled={atEnd}>
                {playing && !atEnd ? "일시정지" : "재생"}
            </button>
            <button onClick={onReset}>처음으로</button>
            <span className="replay-progress">
                {frameIndex+1}/{totalFrames}
            </span>
        </div>
    );
}

export default ReplayControls;