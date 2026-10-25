"use client";

import { useEffect, useState } from "react";
import Card from "@/components/Card";
import SearchBox from "@/components/SearchBox";
import TeamFilter from "@/components/TeamFilter";
import type { Driver } from "@/types";

const teams = ["All", "Mercedes", "Ferrari", "Red Bull", "McLaren"];

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [selectedTeam, setSelectedTeam] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/drivers.json");
        if (!res.ok) throw new Error("서버 오류: " + res.status);
        const data: Driver[] = await res.json();
        setDrivers(data);
      } catch {
        setError("데이터를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const visibleDrivers = drivers.filter((d) => {
    const matchTeam = selectedTeam === "All" || d.team === selectedTeam;
    const matchName = d.name.toLowerCase().includes(search.toLowerCase());
    return matchTeam && matchName;
  });

  return (
    <div>
      <h1>드라이버 목록</h1>
      <SearchBox value={search} onChange={setSearch} />
      <TeamFilter
        teams={teams}
        selectedTeam={selectedTeam}
        onSelect={setSelectedTeam}
      />

      {loading && <p>불러오는 중...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && visibleDrivers.length === 0 && (
        <p>검색 결과가 없어요.</p>
      )}
      {!loading && !error && (
        <div className="row">
          {visibleDrivers.map((d) => (
            <Card key={d.id} name={d.name} team={d.team} number={d.number} />
          ))}
        </div>
      )}
    </div>
  );
}
