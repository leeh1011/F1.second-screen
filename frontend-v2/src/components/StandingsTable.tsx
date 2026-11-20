import type { Standing } from "@/types";

type StandingsTableProps={
    standings: Standing[];
    battleCodes: string[];
};

function StandingsTable({standings,battleCodes}:StandingsTableProps
){
    return (
        <table className="standings">
            <thead>
                <tr>
                    <th>P</th>
                    <th>드라이버</th>
                    <th>앞차 간격</th>
                    <th>타이어</th>
                </tr>
            </thead>
            <tbody>
                {standings.map((s)=>(
                    <tr
                        key={s.code}
                        className={battleCodes.includes(s.code) ? "in-battle" : ""}
                    >
                        <td>{s.position}</td>
                        <td className="driver-code">{s.code}</td>
                        <td>{s.gap_ahead === null ? "-" : `+${s.gap_ahead}`}</td>
                        <td>
                        <span className="tyre">
                            {s.tyre.compound} {s.tyre.age}랩
                        </span>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export default StandingsTable;