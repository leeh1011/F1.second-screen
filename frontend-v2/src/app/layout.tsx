import type { Metadata, Viewport } from "next";
import { Sofia_Sans_Extra_Condensed, IBM_Plex_Sans_KR } from "next/font/google";
import Link from "next/link";
import NavLinks from "@/components/NavLinks";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";
import "./globals.css";

// 숫자·드라이버 코드용 (한글 없음). 방송 그래픽처럼 기울어진 극세폭 글꼴.
const display = Sofia_Sans_Extra_Condensed({
  subsets: ["latin"],
  style: ["italic"],
  variable: "--font-display",
  display: "swap",
});

// 본문·한글 제목용
const body = IBM_Plex_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RaceIQ Overtake",
  description: "F1 중계 옆에 띄워 두는 3랩 내 추월 확률 세컨드 스크린",
  applicationName: "RaceIQ Overtake",
  // 아이폰 사파리에서 "홈 화면에 추가"했을 때 앱처럼 열리게
  appleWebApp: {
    capable: true,
    title: "RaceIQ",
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: "#131619",
};

export default function RootLayout({children,}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={`${display.variable} ${body.variable}`}>
      <body>
        <header className="site-header">
          <div className="site-header-inner">
            <Link href="/" className="wordmark">RaceIQ</Link>
            <NavLinks />
          </div>
        </header>
        <main className="content">{children}</main>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
