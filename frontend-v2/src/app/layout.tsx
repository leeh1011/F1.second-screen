import type { Metadata, Viewport } from "next";
import { Big_Shoulders, IBM_Plex_Sans_KR } from "next/font/google";
import Link from "next/link";
import NavLinks from "@/components/NavLinks";
import "./globals.css";

// 숫자·드라이버 코드용 (한글 없음)
const display = Big_Shoulders({
  subsets: ["latin"],
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
  title: "F1 GG",
  description: "F1 드라이버 정보 서비스",
};

export const viewport: Viewport = {
  themeColor: "#20252b",
};

export default function RootLayout({children,}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={`${display.variable} ${body.variable}`}>
      <body>
        <header className="site-header">
          <div className="site-header-inner">
            <Link href="/" className="wordmark">F1 GG</Link>
            <NavLinks />
          </div>
        </header>
        <main className="content">{children}</main>
      </body>
    </html>
  );
}
