# frontend-v2

RaceIQ Overtake의 새 프론트엔드입니다. (Next.js 16, React 19, TypeScript, App Router)

## 실행 방법

```bash
npm install
npm run dev
```

브라우저에서 http://localhost:3000 을 엽니다.

백엔드와 연결하려면 이 폴더에 `.env.local` 파일을 만들고 다음을 적습니다.
설정하지 않으면 mock 데이터(`public/drivers.json`)로 동작합니다.

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 화면

| 주소 | 화면 |
|---|---|
| `/` | 홈 |
| `/drivers` | 드라이버 목록 (검색, 팀 필터) |
| `/drivers/[id]` | 드라이버 상세 |

## 폴더 구조

```
src/
├── app/
│   ├── layout.tsx          공통 레이아웃 (헤더, 메뉴)
│   ├── page.tsx            홈
│   ├── globals.css         전체 스타일
│   └── drivers/
│       ├── page.tsx        드라이버 목록 (클라이언트 컴포넌트)
│       └── [id]/page.tsx   드라이버 상세 (서버 컴포넌트)
├── components/             Card, SearchBox, TeamFilter
├── lib/api.ts              데이터 가져오기 (mock ↔ 실제 API 전환)
└── types.ts                Driver 타입
docs/api-contract.md        백엔드와 맞출 API 계약서 초안
```

## 검사

```bash
npm run lint
npx tsc --noEmit
```
