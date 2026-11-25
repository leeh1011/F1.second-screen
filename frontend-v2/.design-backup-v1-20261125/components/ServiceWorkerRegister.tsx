"use client";

import { useEffect } from "react";

// 브라우저에 서비스 워커(public/sw.js)를 등록하는 컴포넌트.
// 화면에는 아무것도 그리지 않고, layout에서 한 번만 실행돼요.
export default function ServiceWorkerRegister() {
  useEffect(() => {
    // 개발 서버(npm run dev)에서는 등록하지 않아요. 코드 수정이 바로 안 보이는 문제를 막기 위해서예요.
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.warn("서비스 워커 등록 실패:", err);
    });
  }, []);

  return null;
}
