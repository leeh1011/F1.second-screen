import Link from "next/link";

export default function Home() {
  return (
    <div className="hero">
      <p className="hero-label">RaceIQ Overtake</p>
      <h1>F1 추월 확률 예측 서비스</h1>
      <p className="hero-desc">
        실제 F1 경기 데이터를 바탕으로 차량 간 추월 가능성을 예측하고,
        드라이버 정보를 한눈에 보여 줍니다.
      </p>
      <Link href="/drivers" className="hero-button">
        드라이버 보러 가기
      </Link>
    </div>
  );
}
