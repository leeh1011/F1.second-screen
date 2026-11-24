// 브라우저(시스템) 알림 도우미

export function notificationSupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

// 권한 요청: 반드시 버튼 클릭 같은 사용자 동작 안에서 불러야 해요.
export async function requestNotificationPermission(): Promise<NotificationPermission | "unsupported"> {
  if (!notificationSupported()) return "unsupported";
  if (Notification.permission !== "default") return Notification.permission;
  return Notification.requestPermission();
}

// 알림 띄우기: 서비스 워커가 있으면 그쪽으로 (설치한 앱·휴대폰에서도 동작), 없으면 기본 방식
export async function showSystemNotification(title: string, body: string, tag: string) {
  if (!notificationSupported() || Notification.permission !== "granted") return;

  const options: NotificationOptions = {
    body,
    tag,                               // 같은 tag면 새 알림이 이전 것을 대체
    icon: "/icons/icon-192.png",
    badge: "/icons/icon-192.png",
    data: { url: window.location.href }, // sw.js에서 알림을 누르면 이 주소로 돌아옴
  };

  try {
    const reg = "serviceWorker" in navigator ? await navigator.serviceWorker.getRegistration() : undefined;
    if (reg) await reg.showNotification(title, options);
    else new Notification(title, options);
  } catch (err) {
    console.warn("알림 표시 실패:", err);
  }
}
