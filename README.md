# RaceIQ Overtake

F1 경기 데이터에서 **추월 기회를 추출**하고, ML로 **추월 성공 확률을 예측**해서 보여주는 서비스.
드라이버별 추월 성향(Overtake DNA)도 분석한다.

> 현재 상태: 백엔드 MVP 구현 중 (뼈대 구조만 잡혀 있음)

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy 2.0, SQLite (이후 PostgreSQL) |
| 데이터 / ML | FastF1, pandas, scikit-learn |

## 폴더 구조

```text
f1-gg/
├── frontend/              # Next.js 앱
└── backend/
    ├── app/
    │   ├── main.py        # FastAPI 시작점
    │   ├── database.py    # DB 연결 (engine, SessionLocal, Base)
    │   ├── core/          # 설정 (.env 로드)
    │   ├── api/           # 엔드포인트 (races, overtakes, drivers, prediction)
    │   ├── models/        # SQLAlchemy ORM (Race, Driver, Overtake)
    │   ├── schemas/       # Pydantic 요청/응답
    │   ├── services/      # DB 조회·분석 로직 (온라인)
    │   ├── pipeline/      # FastF1 수집 → 추월 추출 → DB 적재 (오프라인)
    │   ├── ml/            # features / train / predict
    │   └── live/          # Phase 2: 실시간 WebSocket, Gemini 해설 (MVP 이후)
    ├── data/              # cache(FastF1 캐시), processed(parquet), SQLite DB
    └── tests/
```

핵심 원칙: **데이터 수집·학습은 오프라인, API 서버는 DB 조회와 예측만 한다.**

```text
[오프라인] FastF1 → pipeline(수집·추월 추출) → parquet → DB(SQLite)
                                          └→ ml/train → model.pkl
[온라인]   프론트 → FastAPI(api) → services → DB 조회 / ml.predict
```

## 실행 방법

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # DATABASE_URL 등 설정
uvicorn app.main:app --reload # http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
# .env.local 파일을 만들고 아래 값을 작성
npm run dev                        # http://localhost:3000
```

`frontend/.env.local`

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=true   # 백엔드 연결 전에는 true
```

## API (MVP)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 상태 확인 |
| GET | `/api/races?year=2024` | 경기 목록 |
| GET | `/api/races/{race_id}/overtakes` | 경기별 추월 기회 목록 |
| GET | `/api/overtakes/{overtake_id}` | 추월 상세 |
| POST | `/api/prediction/overtake` | 추월 성공 확률 예측 |
| GET | `/api/drivers` | 드라이버 목록 |
| GET | `/api/drivers/{code}/dna` | 드라이버 Overtake DNA |

응답 필드는 snake_case로 통일한다. (예: `speed_diff_kph`, `success_rate`)

## 용어 정의

- **추월 기회**: 공격자가 수비자 바로 뒤 1.0초 이내이고, SC/VSC·피트 인/아웃랩이 아닌 구간
- **SUCCESS**: 이후 1~2랩 안에 순위가 역전됨 (피트스톱으로 인한 역전 제외)
- **FAIL**: 그 외
- **Overtake DNA**: `success_rate`(성공/시도), `preferred_zone`(성공이 가장 많은 구간), `drs_dependency`(성공 중 DRS 비율), `aggression`(경기당 시도 횟수의 상대 순위)

## 구현 순서 (진행 체크)

- [ ] 1. DB 연결 + ORM 모델 3개 (SQLite)
- [ ] 2. 한 경기 파이프라인 (FastF1 → 추월 추출 → DB 적재)
- [ ] 3. 경기 목록 / 추월 목록·상세 API
- [ ] 4. 실데이터 기반 모델 학습 + 예측 API
- [ ] 5. Driver DNA API
- [ ] 6. 프론트 연결 (mock → 실제 API)

## 협업 규칙

- `main`에 직접 푸시하지 말고 브랜치(`feature/기능명`)에서 작업 후 PR
- 커밋 메시지는 무엇을 했는지 한 줄로 명확하게
- `.env`, `venv/`, `data/*.db`, `data/cache/`는 커밋하지 않는다
- 모델 변경(컬럼 추가 등)은 팀원에게 공유 (개발 중에는 `data/f1gg.db`를 지우고 재생성)
