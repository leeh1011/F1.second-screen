# API 계약서 (합의본 v1)

프론트엔드(frontend-v2)와 백엔드(backend)가 합의한 데이터 형태입니다.
응답 필드는 snake_case를 사용합니다.

- 백엔드 기본 주소: `http://localhost:8000`
- 프론트 설정: `frontend-v2/.env.local` 에 `NEXT_PUBLIC_API_URL=http://localhost:8000`
- 이 값이 없으면 프론트는 mock 데이터(`public/drivers.json`)를 사용합니다.

> 현재 확인된 백엔드 진행: 2024년 첫 8경기 데이터 확장과 시간순 학습·평가까지.
> 학습 모델과 예측 API의 완전한 연동은 아직 완료되지 않았습니다.

## 1. 드라이버 식별자 — 프론트 `id` 유지 + `code` 추가

- 프론트 주소는 숫자 `id`를 유지합니다: `/drivers/{id}`, `/api/drivers/{id}/dna`
- 목록 응답에 `code`를 추가합니다.

```ts
type Driver = {
  id: number;     // 서비스에서 드라이버를 식별하는 고유 번호
  code: string;   // VER, NOR 같은 표시용 코드
  name: string;
  team: string;
  number: number; // 해당 시즌·경기의 차량 번호
};
```

- 주의: 프론트 `id`와 OpenF1 `driver_number`는 같은 값이 아닙니다.
  백엔드에서 서비스 `id`와 경기별 OpenF1 드라이버 번호를 연결합니다. (매핑은 아직 확정 전)

## 2. 단건 조회 API — 지금은 추가하지 않음

- `GET /api/drivers` 목록을 받아 프론트에서 `id`로 찾습니다.
- 상세 정보가 늘어나면 `GET /api/drivers/{id}`를 추가합니다.
- DNA API는 주소 규칙만 정하고, 계산 방식과 응답 필드는 별도로 설계합니다.

## 3. 오류 응답 — `detail` 사용, 예측 불가와 0%를 구분

```json
{ "detail": "해당 관측 시점에는 예측에 필요한 데이터가 부족합니다." }
```

| 상태 코드 | 의미 |
|---|---|
| 200 | 정상 조회·예측 |
| 404 | 요청한 드라이버·배틀·관측 데이터 없음 |
| 422 | 입력 오류 또는 해당 관측의 예측 조건 미충족 |
| 503 | 모델이 준비되지 않아 예측 불가 |
| 500 | 예상하지 못한 내부 오류 |

- 예측할 수 없는 상황을 `probability: 0`으로 보내지 않습니다. 0%와 "계산 불가"는 다른 의미입니다.
- 입력 검증 오류(422)는 `detail`이 배열로 올 수 있으므로 프론트는 문자열·배열 모두 처리합니다.

## 4. 예측 API — 저장된 배틀의 특정 관측을 선택

```
프론트에서 배틀·관측 시점 선택
→ 백엔드에서 해당 관측의 피처 조회
→ 학습 모델에 입력
→ 3랩 이내 추월 확률 반환
```

`POST /api/prediction/overtake`

요청:
```json
{ "battle_id": "배틀 식별자", "prediction_time": "관측 시각" }
```

응답 (값은 형식 예시):
```json
{
  "battle_id": "배틀 식별자",
  "prediction_time": "관측 시각",
  "target": "target_overtake_3lap",
  "probability": 0.72
}
```

- 프론트는 피처를 계산하지 않고, 목록 API에서 받은 `battle_id`와 `prediction_time`을 그대로 보냅니다.
- 두 필드로 관측을 하나로 찾을 수 있는지는 연동 전에 확인합니다.
- 연결 대상은 `target_overtake_3lap` 하나입니다. 코너별 예측과 5랩 예측은 이번 계약에 넣지 않습니다.
- `probability`는 0~1이며, 화면에는 백분율과 함께 **"모델 예측 확률"**로 표시합니다. (확률 보정 전)
- 3랩 종료 기준은 라벨 생성 코드와 같게 문서화합니다.
- 실제 추월 사건의 `overtake_id`와 추월이 일어나지 않을 수도 있는 후보의 `battle_id`는 구분합니다.
  `/api/races/{race_id}/overtakes`가 실제 추월 목록이라면, 예측할 배틀 후보 목록 API는 따로 정합니다. (미정)

## 5. CORS — 기존 설정에 프론트 주소 포함 여부 확인

- 백엔드는 이미 CORS 미들웨어와 `settings.CORS_ORIGINS`를 사용합니다.
- 이 값에 `http://localhost:3000`이 있는지 확인하고, 없으면 추가합니다.

## 아직 정할 것

1. 배틀 후보 목록 API의 주소와 응답 필드 (`battle_id`, `prediction_time` 목록)
2. 서비스 `id` ↔ OpenF1 `driver_number` 매핑 방식
3. DNA 계산 방식과 응답 필드
