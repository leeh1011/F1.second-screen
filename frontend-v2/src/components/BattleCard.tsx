import type {Battle} from "@/types";

type BattleCardProps={
    battle:Battle,
};

function BattleCard({battle}:BattleCardProps){
    const {
    attacker_code, defender_code, attacker_position,
    gap, attacker_tyre, defender_tyre, probability,
    } = battle;

    const defenderPosition = attacker_position - 1;

    return (
    <div className="battle-card">
      <div className="battle-info">
        <p className="battle-drivers">
          P{attacker_position} {attacker_code}
          <span className="arrow"> → </span>
          P{defenderPosition} {defender_code}
        </p>
        <p className="battle-tyres">
          <span className="tyre">{attacker_tyre.compound} {attacker_tyre.age}랩</span>
          <span className="tyre">{defender_tyre.compound} {defender_tyre.age}랩</span>
        </p>
        <p className="battle-gap">간격 {gap}초</p>
      </div>

      <div className="battle-prob">
        {probability === null ? (
          <span className="prob-na">계산 불가</span>
        ) : (
          <span className="prob">{Math.round(probability * 100)}%</span>
        )}
        <span className="prob-label">3랩 내 추월</span>
      </div>
    </div>
  );
}

export default BattleCard;