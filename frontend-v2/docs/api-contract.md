# API 계약서 (초안)

프론트엔드(frontend-v2)와 백엔드(backend)가 주고받을 데이터 형태를 정리한 문서입니다.
엔드포인트 목록은 저장소 README의 "API (MVP)"를 기준으로 했고,
응답 필드는 README 규칙에 따라 snake_case를 사용합니다.

- 백엔드 기본 주소: `http://localhost:8000`
- 프론트 설정: `frontend-v2/.env.local` 에 `NEXT_PUBLIC_API_URL=http://localhost:8000`
- 이 값이 없으면 프론트는 mock 데이터(`public/drivers.json`)를 사용합니다.

## 엔드포인트

| 메서드 | 경로 | 설명 | 프론트 사용 화면 |
|---|---|---|---|
| GET | `/api/health` | 서버 상태 확인 | - |
| GET | `/api/races?year=2024` | 시즌별 경기 목록 | (예정) 경기 목록 |
| GET | `/api/races/{race_id}/overtakes` | 경기별 추월 상황 목록 | (예정) 경기 상세 |
| GET | `/api/overtakes/{overtake_id}` | 추월 상황 상세 | (예정) 추월 상세 |
| POST | `/api/prediction/overtake` | 추월 성공 확률 예측 | (예정) 예측 화면 |
| GET | `/api/drivers` | 드라이버 목록 | `/drivers`, `/drivers/[id]` |
| GET | `/api/drivers/{code}/dna` | 드라이버 Overtake DNA | (예정) 드라이버 상세 |

## 현재 프론트에서 사용하는 응답 형태

### GET /api/drivers

```json
[
  { "id": 1, "name": "Kimi Antonelli", "team": "Mercedes", "number": 1 }
]
```

프론트 타입 (`src/types.ts`):

```ts
type Driver = {
  id: number;
  name: string;
  team: string;
  number: number;
};
```

## 백엔드와 합의가 필요한 항목

1. 드라이버 식별자: 프론트는 `id`(숫자)를 쓰고, README의 DNA API는 `code`(예: VER)를 씁니다. 응답에 `code`를 추가할지, 어느 값을 주소에 쓸지 정해야 합니다.
2. 드라이버 한 명 조회 API(`/api/drivers/{id}`)를 따로 만들지, 목록에서 찾을지 정해야 합니다. (현재 프론트는 목록에서 찾습니다.)
3. 오류 응답 형태 (예: `{ "detail": "..." }`) 와 상태 코드.
4. 예측 API의 요청 본문과 응답 필드 (예: `probability` 0~1 값).
5. 프론트 개발 서버(localhost:3000)에서 요청할 수 있도록 백엔드 CORS 허용.
