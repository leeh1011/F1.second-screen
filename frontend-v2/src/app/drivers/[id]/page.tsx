import type { CSSProperties } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import TeamTheme from "@/components/TeamTheme";
import { getDriver } from "@/lib/api";
import { themeFor } from "@/lib/teams";

export default async function DriverDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const driver = await getDriver(Number(id));

  if (!driver) notFound();

  const theme = themeFor(driver.team);

  return (
    <div className="detail">
      <TeamTheme team={driver.team} />
      <Link href="/drivers" className="back-link">
        ← 목록으로
      </Link>
      <section
        className="driver-hero"
        style={{ "--team": theme.accent, "--on-team": theme.on } as CSSProperties}
      >
        <span className="driver-hero-number">{driver.number}</span>
        <div>
          <h1 className="driver-hero-name">{driver.name}</h1>
          <p className="driver-hero-meta">
            <span className="driver-tag">{driver.code}</span>
            {driver.team}
          </p>
        </div>
      </section>
    </div>
  );
}
