import type { MetadataRoute } from "next";

// PWA 매니페스트: Next.js가 /manifest.webmanifest 로 자동 제공해요.
// 휴대폰·PC에서 "홈 화면에 추가 / 앱 설치"를 하면 이 정보로 앱처럼 열려요.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "RaceIQ Overtake",
    short_name: "RaceIQ",
    description: "F1 중계 옆에 띄워 두는 3랩 내 추월 확률 세컨드 스크린",
    start_url: "/",
    scope: "/",
    display: "standalone", // 주소창 없이 앱처럼 열기
    orientation: "any",
    background_color: "#131619", // --tarmac
    theme_color: "#131619",
    lang: "ko",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      // maskable: 안드로이드가 원·둥근 사각형으로 잘라도 글자가 안 잘리게 여백을 둔 버전
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
