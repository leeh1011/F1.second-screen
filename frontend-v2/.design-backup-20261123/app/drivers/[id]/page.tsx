import Link from "next/link";
import { notFound } from "next/navigation";
import { getDriver } from "@/lib/api";

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
      <div className="detail-card">
        <span className="number">{driver.number}</span>
        <h1>{driver.name}</h1>
        <p>Team: {driver.team}</p>
      </div>
    </div>
  );
}
