import type { Standing } from "@/types";
import TyreMark from "./TyreMark";

type StandingsTableProps = {
  standings: Standing[];
  battleCodes: string[];
};

function StandingsTable({ standings, battleCodes }: StandingsTableProps) {
  return (
    <table className="tower">
      <caption className="sr-only">현재 순위. 보라색으로 표시된 줄은 추월 배틀 중인 드라이버입니다.</caption>
      <thead>
        <tr>
          <th scope="col">P</th>
          <th scope="col">드라이버</th>
          <th scope="col" className="tower-num">앞차와 간격</th>
          <th scope="col">타이어</th>
        </tr>
      </thead>
      <tbody>
        {standings.map((s) => {
          const inBattle = battleCodes.includes(s.code);
          return (
            <tr key={s.code} className={inBattle ? "tower-row-battle" : undefined}>
              <td className="tower-pos">{s.position}</td>
              <td className="tower-code">
                {s.code}
                {inBattle && <span className="sr-only"> 배틀 중</span>}
              </td>
              <td className="tower-num tower-gap">
                {s.gap_ahead === null ? "-" : `+${s.gap_ahead}`}
              </td>
              <td>
                <TyreMark tyre={s.tyre} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export default StandingsTable;
