import type { CSSProperties } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getDriver } from "@/lib/api";
import { teamColor } from "@/lib/teams";

export default async function DriverDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const driver = await getDriver(Number(id));

  if (!driver) notFound();

  return (
    <div className="detail">
      <Link href="/drivers" className="back-link">
        ← 목록으로
      </Link>
      <section
        className="driver-hero"
        style={{ "--team": teamColor(driver.team) } as CSSProperties}
      >
        <span className="driver-hero-number">{driver.number}</span>
        <div>
          <h1 className="driver-hero-name">{driver.name}</h1>
          <p className="driver-hero-meta">{driver.team}, {driver.code}</p>
        </div>
      </section>
    </div>
  );
}
