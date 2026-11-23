"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Card from "@/components/Card";
import SearchBox from "@/components/SearchBox";
import TeamFilter from "@/components/TeamFilter";
import { getDrivers } from "@/lib/api";
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
        const data = await getDrivers();
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
      <div className="page-head">
        <h1 className="page-title">드라이버</h1>
        {!loading && !error && (
          <span className="page-count">{visibleDrivers.length}명</span>
        )}
      </div>
      <div className="tools">
        <SearchBox value={search} onChange={setSearch} />
        <TeamFilter
          teams={teams}
          selectedTeam={selectedTeam}
          onSelect={setSelectedTeam}
        />
      </div>

      {loading && <p className="state-note">불러오는 중...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && visibleDrivers.length === 0 && (
        <p className="state-note">
          조건에 맞는 드라이버가 없어요. 검색어나 팀을 바꿔 보세요.
        </p>
      )}
      {!loading && !error && visibleDrivers.length > 0 && (
        <div className="driver-list">
          {visibleDrivers.map((d) => (
            <Link key={d.id} href={`/drivers/${d.id}`} className="card-link">
              <Card name={d.name} team={d.team} number={d.number} code={d.code} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
