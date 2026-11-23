// RaceIQ Overtake 서비스 워커
// 지금은 "설치 가능한 앱"이 되기 위한 최소 구성만 있어요.
// 8주차에 추월 확률 알림(브라우저 알림)을 여기에 추가할 예정이에요.
// 예측 데이터는 항상 최신이어야 하므로 화면·데이터를 캐시하지 않아요.

self.addEventListener("install", () => {
  // 새 버전이 오면 기다리지 않고 바로 교체
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// 알림을 누르면 열려 있는 앱 창으로 이동 (8주차 알림 기능용 준비)
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ("focus" in client) return client.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
