import type { OvertakeAlert } from "@/lib/alerts";

type AlertToastProps = {
  alerts: OvertakeAlert[];
  onSelect: (battleId: string) => void;
};

// 화면 오른쪽 위에 뜨는 알림 (시스템 알림이 꺼져 있어도 보이게)
function AlertToast({ alerts, onSelect }: AlertToastProps) {
  if (alerts.length === 0) return null;
  return (
    <div className="toasts" role="status" aria-live="polite">
      {alerts.map((a) => (
        <div key={a.key} className={`toast toast-${a.kind}`}>
          <p className="toast-title">{a.title}</p>
          <p className="toast-body">{a.body}</p>
          {a.battleId && (
            <button className="toast-link" onClick={() => onSelect(a.battleId!)}>자세히 보기</button>
          )}
        </div>
      ))}
    </div>
  );
}

export default AlertToast;
