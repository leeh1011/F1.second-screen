import Link from "next/link";
import BattleCard from "@/components/BattleCard";
import { getReplay } from "@/lib/api";

export default async function Home() {
  // 리플레이 첫 장면에서 확률이 가장 높은 배틀을 예시로 보여 준다
  const replay = await getReplay();
  const first = replay.frames[0];
  const sample = first.battles
    .filter((b) => b.probability !== null)
    .sort((a, b) => (b.probability ?? 0) - (a.probability ?? 0))[0];

  return (
    <div className="hero">
      <div>
        <h1 className="hero-title">
          앞차와 1초 안으로 붙었다면, 3랩 안에 추월할 수 있을까요?
        </h1>
        <p className="hero-desc">
          중계 화면 옆에 띄워 두세요. 지금 붙어 있는 차들의 간격과 타이어 상태를 보여 주고,
          모델이 예측한 추월 확률을 랩마다 알려 줘요.
        </p>
        <div className="hero-actions">
          <Link href="/live" className="btn btn-primary">라이브 화면 보기</Link>
          <Link href="/drivers" className="btn btn-quiet">드라이버 보기</Link>
        </div>
      </div>

      {sample && (
        <div>
          <BattleCard battle={sample} prevProbability={null} featured />
          <p className="hero-sample-note">
            {first.race_name} {first.lap}랩 장면 예시
          </p>
        </div>
      )}
    </div>
  );
}
