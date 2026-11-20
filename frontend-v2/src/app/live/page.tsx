"use client";

import {useEffect,useState} from "react";
import LiveHeader from "@/components/LiveHeader";
import { getLiveState } from "@/lib/api";
import type { LiveState } from "@/types";
import BattleCard from "@/components/BattleCard";
import EventFeed from "@/components/EventFeed";
import StandingsTable from "@/components/StandingsTable";

export default function LivePage(){
    const [state,setState]=useState<LiveState|null>(null);

    useEffect(()=>{
        async function load(){
            const data=await getLiveState();
            setState(data);
        }
        load();
    },[]);

    if(!state){
        return <p>불러오는 중...</p>
    }

    const top3 = state.battles
       .filter((b) => b.probability !== null)
       .sort((a, b) => (b.probability ?? 0) - (a.probability ?? 0))
       .slice(0, 3);

    const battleCodes = top3.flatMap((b) => [b.attacker_code, b.defender_code]);
    
    return (
        <div>
            <LiveHeader liveState={state} />
            <div className="battle-list">
            {top3.map((b) => (
                <BattleCard key={b.battle_id} battle={b} />
            ))}
            </div>
            <h3>순위표</h3>
            <StandingsTable standings={state.standings} battleCodes={battleCodes} />
            <h3>최근 이벤트</h3>
            <EventFeed events={state.events} />
        </div>
    );
}