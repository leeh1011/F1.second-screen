import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "F1 GG",
  description: "F1 드라이버 정보 서비스",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <header className="header">
          <Link href="/">F1 GG</Link>
          <nav>
            <Link href="/">홈</Link>
            <Link href="/drivers">드라이버</Link>
          </nav>
        </header>
        <main className="content">{children}</main>
      </body>
    </html>
  );
}