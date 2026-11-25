type AlertSettingsProps = {
  enabled: boolean;
  threshold: number;                                  // 0~1
  permission: NotificationPermission | "unsupported";
  onToggle: () => void;
  onThresholdChange: (value: number) => void;
};

const OPTIONS = [0.6, 0.7, 0.75, 0.8];

// 추월 알림 켜기/끄기 + 기준 확률 고르기
function AlertSettings({ enabled, threshold, permission, onToggle, onThresholdChange }: AlertSettingsProps) {
  let note = "확률이 기준을 넘거나 추월·세이프티카가 나오면 알려 드려요.";
  if (enabled && permission === "granted") note = "알림 켜짐 · 다른 창을 보고 있어도 시스템 알림이 와요.";
  if (enabled && permission === "denied") note = "브라우저에서 알림이 차단돼 있어 화면 안에서만 알려 드려요.";
  if (enabled && permission === "unsupported") note = "이 브라우저는 시스템 알림을 지원하지 않아 화면 안에서만 알려 드려요.";

  return (
    <div className="alert-settings" role="group" aria-label="추월 알림 설정">
      <button
        className={`alert-toggle${enabled ? " alert-toggle-on" : ""}`}
        onClick={onToggle}
        aria-pressed={enabled}
      >
        {enabled ? "알림 켜짐" : "추월 알림 받기"}
      </button>
      <label className="alert-threshold">
        기준
        <select
          value={threshold}
          onChange={(e) => onThresholdChange(Number(e.target.value))}
          disabled={!enabled}
        >
          {OPTIONS.map((o) => (
            <option key={o} value={o}>{Math.round(o * 100)}% 이상</option>
          ))}
        </select>
      </label>
      <p className="alert-note">{note}</p>
    </div>
  );
}

export default AlertSettings;
