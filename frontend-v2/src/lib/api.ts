import type { Driver } from "@/types";
import mockDrivers from "../../public/drivers.json";

// 백엔드 주소. 설정하지 않으면 mock 데이터를 사용한다.
// 예) .env.local 에 NEXT_PUBLIC_API_URL=http://localhost:8000
const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error("서버 오류: " + res.status);
  return res.json();
}

// 드라이버 목록: GET /api/drivers
export async function getDrivers(): Promise<Driver[]> {
  if (!API_URL) return mockDrivers as Driver[];
  return request<Driver[]>("/api/drivers");
}

// 드라이버 한 명: 목록에서 id로 찾는다 (상세 API가 생기면 교체)
export async function getDriver(id: number): Promise<Driver | undefined> {
  const drivers = await getDrivers();
  return drivers.find((d) => d.id === id);
}
