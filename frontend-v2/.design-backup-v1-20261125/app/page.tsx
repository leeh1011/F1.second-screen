import Link from "next/link";
import BattleCard from "@/components/BattleCard";
import { getReplay, getReplayList } from "@/lib/api";

export default async function Home() {
  const replays = await getReplayList();

  // 리플레이 첫 장면에서 확률이 가장 높은 배틀을 예시로 보여 준다
  const replay = await getReplay();
  const first = replay?.frames[0];
  const sample = first?.battles
    .filter((b) => b.probability !== null)
    .sort((a, b) => (b.probability ?? 0) - (a.probability ?? 0))[0];

  return (
    <div className="home">
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
            <Link href="/live?race=2024-bahrain" className="btn btn-primary">리플레이 바로 보기</Link>
            <Link href="/drivers" className="btn btn-quiet">드라이버 보기</Link>
          </div>
        </div>

        {first && sample && (
          <div>
            <BattleCard battle={sample} prevProbability={null} featured />
            <p className="hero-sample-note">
              {first.race_name} {first.lap}랩 장면 예시
            </p>
          </div>
        )}
      </div>

      <section className="start" aria-labelledby="start-title">
        <h2 id="start-title" className="section-title">경기 고르기</h2>

        <div className="start-live">
          <span className="start-live-dot" aria-hidden="true" />
          <div>
            <p className="start-live-title">실시간 경기</p>
            <p className="start-live-desc">
              지금 진행 중인 경기가 없어요. 실시간 데이터 연동은 준비 중이라, 아래 리플레이로 먼저 체험해 보세요.
            </p>
          </div>
        </div>

        <ul className="replay-list">
          {replays.map((r) => (
            <li key={r.id}>
              {r.available ? (
                <Link href={`/live?race=${r.id}`} className="replay-item">
                  <span className="replay-item-name">{r.race_name}</span>
                  <span className="replay-item-laps">{r.laps}</span>
                  <span className="replay-item-summary">{r.summary}</span>
                  <span className="replay-item-go">재생 →</span>
                </Link>
              ) : (
                <div className="replay-item replay-item-off" aria-disabled="true">
                  <span className="replay-item-name">{r.race_name}</span>
                  <span className="replay-item-laps">준비 중</span>
                  <span className="replay-item-summary">{r.summary}</span>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
