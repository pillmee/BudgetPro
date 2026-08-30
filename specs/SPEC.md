# BudgetPro 구현 명세서

> 이 문서는 2026-08-31 기준 저장소(`main` 브랜치)의 실제 구현 내용을 기술한 스펙 문서입니다.
> 코드가 변경되면 이 문서도 함께 갱신되어야 합니다.

## 1. 개요

BudgetPro는 팀 단위로 인당 예산을 배정하고, 팀원들이 등록한 지출을 집계하여
잔여 예산을 대시보드로 보여주는 FastAPI 기반 웹 애플리케이션이다.

- 백엔드: FastAPI + Pydantic v2
- 데이터 저장: SQLite (`data/budgetpro.db`)
- 프런트엔드: Jinja2 템플릿(`templates/`) + 정적 JS/CSS(`static/`), SPA가 아닌 서버 렌더 + fetch API 조합
- 인증: 없음 (아래 6장 참조)

## 2. 기술 스택 / 의존성

`requirements.txt` 기준:

| 패키지 | 용도 |
|---|---|
| fastapi | 웹 프레임워크 / 라우팅 |
| uvicorn[standard] | ASGI 서버 |
| pydantic | 데이터 모델 / 검증 |
| python-multipart | 파일 업로드(`UploadFile`) 파싱 |
| jinja2 | `Jinja2Templates` 서버 렌더링 |

DB 접근은 표준 라이브러리 `sqlite3`만 사용하며 별도 ORM은 사용하지 않는다.

## 3. 디렉토리 구조

```text
BudgetPro/
├─ main.py                  # FastAPI 앱 생성, 라우터 등록, HTML 라우트, 서버 실행
├─ requirements.txt
├─ app/
│  ├─ models.py             # Pydantic 모델 (요청/응답 스키마)
│  ├─ utils.py              # SQLite 저장소 계층 (schema, load/save, 조회 헬퍼)
│  ├─ budget_calculator.py  # 예산 초기화/누적/사이클 계산 로직
│  └─ api/
│     ├─ teams.py           # 팀 CRUD
│     ├─ members.py         # 팀원 CRUD
│     ├─ expenses.py        # 지출 CRUD
│     ├─ auth.py            # 로그인, 대시보드 집계
│     └─ settings.py        # 팀 설정, 예산 초기화, 지출 백업/복구
├─ templates/                # index.html, login.html, dashboard.html
├─ static/                   # css/js
└─ data/                     # SQLite DB 파일 (git ignore 대상)
```

## 4. 데이터 모델 (`app/models.py`)

### 4.1 열거형

- `BudgetCycle`: `monthly` | `quarterly` | `half-yearly` | `yearly`
- `ExpenseCategory`: `회식`(DINING) | `음료`(BEVERAGE) | `사무용품`(OFFICE_SUPPLIES) | `기타`(OTHER)

### 4.2 팀 / 팀원

| 모델 | 필드 |
|---|---|
| `Member` | `id`, `name`, `created_at`(기본값 now) |
| `MemberCreate` | `name` |
| `MemberUpdate` | `name` |
| `Team` | `id`, `name`, `per_person_amount`(기본 100000), `budget_cycle`(기본 monthly), `members: List[Member]`, `created_at`, `last_reset_date` |
| `TeamCreate` | `name`, `per_person_amount`(기본 100000), `budget_cycle`(기본 monthly) |
| `TeamUpdate` | `name?`, `per_person_amount?`, `budget_cycle?` (모두 optional, 부분 수정용) |

### 4.3 지출

| 모델 | 필드 |
|---|---|
| `Expense` | `id`, `team_id`, `member_id`, `member_name`(등록 당시 스냅샷), `category`, `description`(기본 `""`), `supply_amount`(공급가액), `vat`(부가세), `total_amount`, `created_at` |
| `ExpenseCreate` | `team_id`, `member_id`, `category`, `description?`, `total_amount`(부가세 포함 총액) |
| `ExpenseResponse` | `Expense`와 동일 (별칭) |

### 4.4 로그인 / 대시보드 / 설정

| 모델 | 필드 |
|---|---|
| `LoginRequest` | `team_id`, `member_id` |
| `LoginResponse` | `team_id`, `team_name`, `member_id`, `member_name`, `token` |
| `Dashboard` | `accumulated_budget`, `total_spent`, `supply_amount_spent`, `vat_spent`, `remaining_budget`, `remaining_budget_without_vat`, `current_month`, `budget_cycle_info`, `member_expenses: List[dict]` |
| `Settings` | `per_person_amount`, `budget_cycle` |

## 5. 데이터 저장소 (`app/utils.py`)

SQLite 파일: `data/budgetpro.db`. 스키마는 앱 최초 호출 시 `_ensure_initialized()`가 지연 생성한다.

### 5.1 테이블

**teams**

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | TEXT PK | UUID |
| name | TEXT | |
| per_person_amount | INTEGER | |
| budget_cycle | TEXT | enum 값 문자열 |
| created_at | TEXT | ISO8601 |
| last_reset_date | TEXT | ISO8601 |

**members**

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | TEXT PK | UUID |
| team_id | TEXT | FK 제약 없음(논리적 참조만) |
| name | TEXT | |
| created_at | TEXT | ISO8601 |

**expenses**

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | TEXT PK | UUID |
| team_id | TEXT | FK 제약 없음 |
| member_id | TEXT | FK 제약 없음 |
| member_name | TEXT | 등록 당시 이름 스냅샷 |
| category | TEXT | enum 값(한글) |
| description | TEXT | nullable |
| supply_amount | INTEGER | |
| vat | INTEGER | |
| total_amount | INTEGER | |
| created_at | TEXT | ISO8601 |

### 5.2 저장 방식

- `load_teams()` / `load_expenses()`: 테이블 전체를 조회해 Pydantic 모델 리스트로 반환. `members`는 `team_id`로 그룹핑해 `Team.members`로 조립.
- `save_teams(teams)` / `save_expenses(expenses)`: **전체 교체** 방식. 대상 테이블을 `DELETE FROM ...`으로 비운 뒤, 인자로 받은 전체 리스트를 다시 INSERT한다. API 레이어가 "전체 로드 → 메모리에서 수정 → 전체 저장"하는 패턴을 그대로 유지하기 위함.
- `get_team_by_id`, `get_member_by_id`: `load_teams()` 결과를 순회하여 조회하는 헬퍼(별도 인덱스 없음, O(n)).
- **팀 삭제 시 연쇄 삭제 없음**: 팀을 삭제해도 해당 팀의 `expenses`, `members` 레코드는 자동으로 정리되지 않는다(기존 JSON 파일 구현부터 이어진 동작).

### 5.3 레거시 마이그레이션

- DB 파일(`data/budgetpro.db`)이 존재하지 않는 상태로 최초 접근 시, `data/teams.json` / `data/expenses.json`이 있으면 읽어서 그대로 SQLite로 이전한다.
- 이전 후에도 원본 JSON 파일은 삭제하지 않고 그대로 남겨둔다.
- 마이그레이션은 1회성이며, DB 파일이 이미 존재하면 다시 수행되지 않는다.

## 6. 인증 모델 (매우 단순함 — 주의)

- `POST /api/auth/login`은 `team_id`/`member_id`가 실존하는지만 확인하고, `uuid4()` 문자열을 `token`으로 발급한다.
- **발급된 토큰은 서버 어디에도 저장/검증되지 않는다.** 이후 어떤 API 요청도 이 토큰을 요구하거나 검사하지 않는다. 즉 인증/인가는 실질적으로 없음.
- 프런트엔드(`templates/login.html`)는 토큰과 `currentMemberId`를 `localStorage`에 저장해 두고 클라이언트 화면 전환에만 사용한다.
- **관리자 로그인**: `login.html`의 "관리자로 로그인"은 `/api/auth/login`을 호출하지 않고, 클라이언트에서 `currentMemberId = 'admin'`, `authToken = 'admin-token'`을 직접 `localStorage`에 세팅한 뒤 `/dashboard`로 이동하는 순수 프런트엔드 동작이다.
- `member_id === 'admin'`은 지출 등록 화면(`static/js/dashboard.js`)과 지출 생성 API(`app/api/expenses.py`) 양쪽에서 특별 취급되어, 관리자 모드에서는 지출을 등록할 수 없고 400 에러(`"관리자 모드에서는 지출을 등록할 수 없습니다..."`)를 반환한다.

## 7. 예산 계산 로직 (`app/budget_calculator.py`)

### 7.1 예산 초기화 여부 판단 — `should_reset_budget(team)`

1. **연말 강제 초기화**: 현재 월이 12월이고, `last_reset_date`의 연/월이 현재와 다르면 사이클과 무관하게 무조건 `True`.
2. 그 외에는 `team.budget_cycle`에 따라 `last_reset_date` 대비 다음 조건으로 판단:
   - `MONTHLY`: 연 또는 월이 다르면 초기화
   - `QUARTERLY`: `(month-1)//3`으로 계산한 분기 또는 연이 다르면 초기화
   - `HALF_YEARLY`: 1~6월/7~12월 반기 또는 연이 다르면 초기화
   - `YEARLY`: 연이 다르면 초기화

호출 위치: `GET /api/auth/dashboard/{team_id}` — 조건이 참이면 해당 팀의 모든 지출을 삭제하고 `last_reset_date`를 현재 시각으로 갱신한 뒤 대시보드를 계산한다(자동 초기화).

### 7.2 누적 예산 계산 — `calculate_accumulated_budget(team)`

```
accumulated_budget = per_person_amount × 팀원 수 × 현재 월(1~12)
```

- 매년 1월부터 현재 월까지 매월 누적된다는 명세를 따르며, `budget_cycle` 설정과 무관하게 항상 "현재 연도 1월부터 현재 월까지의 누적"으로 계산한다.
- 즉 8월이면 8개월치가 누적된 값이 예산으로 잡힌다.

### 7.3 사이클 표시 문자열 — `get_cycle_info(team)`

| budget_cycle | 반환 예시 |
|---|---|
| monthly | `2026년 08월` |
| quarterly | `2026년 3분기` |
| half-yearly | `2026년 상반기` / `2026년 하반기` |
| yearly | `2026년` |

## 8. API 명세

공통 사항:
- 모든 API는 `/api` 하위에 마운트되며 라우터별 prefix는 `main.py`에서 지정.
- 리소스 없음(404) 시 `{"detail": "..."}` 형태의 한국어 메시지 반환(FastAPI 표준 오류 포맷).
- 인증 검사는 없음(6장 참조) — 모든 엔드포인트는 사실상 공개 API.

### 8.1 Teams (`/api/teams`, `app/api/teams.py`)

| Method | Path | 설명 | 비고 |
|---|---|---|---|
| GET | `/api/teams` | 전체 팀 목록 | |
| GET | `/api/teams/{team_id}` | 팀 단건 조회 | 없으면 404 |
| POST | `/api/teams` | 팀 생성 | `id`는 서버에서 `uuid4()` 생성, `members=[]`로 시작 |
| PUT | `/api/teams/{team_id}` | 팀 부분 수정 | `TeamUpdate`의 non-null 필드만 반영 |
| DELETE | `/api/teams/{team_id}` | 팀 삭제 | 소속 팀원/지출은 함께 삭제되지 않음 |

### 8.2 Members (`/api/members`, `app/api/members.py`)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/members/{team_id}` | 팀의 팀원 목록 |
| GET | `/api/members/{team_id}/{member_id}` | 팀원 단건 조회 |
| POST | `/api/members/{team_id}` | 팀원 추가 (`id`는 `uuid4()`) |
| PUT | `/api/members/{team_id}/{member_id}` | 팀원 이름 수정 |
| DELETE | `/api/members/{team_id}/{member_id}` | 팀원 삭제 (해당 팀원의 기존 지출 기록은 유지됨) |

### 8.3 Expenses (`/api/expenses`, `app/api/expenses.py`)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/expenses?team_id=` | 지출 목록 (team_id로 선택적 필터) |
| GET | `/api/expenses/{expense_id}` | 지출 단건 조회 |
| POST | `/api/expenses` | 지출 등록 |
| DELETE | `/api/expenses/{expense_id}` | 지출 삭제 |

**지출 등록 규칙 (`POST /api/expenses`)**:
1. `team_id`가 존재해야 함 (없으면 404)
2. `member_id == "admin"`이면 400 에러 (관리자는 지출 등록 불가)
3. `member_id`가 해당 팀의 실제 팀원이어야 함 (없으면 404)
4. 부가세 계산: `supply_amount = int(total_amount / 1.1)`, `vat = total_amount - supply_amount`
5. `member_name`은 등록 시점의 팀원 이름을 스냅샷으로 저장 (이후 팀원 이름이 바뀌어도 과거 지출 기록의 이름은 바뀌지 않음)

### 8.4 Auth / Dashboard (`/api/auth`, `app/api/auth.py`)

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/auth/login` | 팀/팀원 존재 확인 후 임시 토큰 발급(6장 참조) |
| GET | `/api/auth/dashboard/{team_id}` | 대시보드 데이터 조회 (자동 예산 초기화 포함) |

**대시보드 계산 순서**:
1. 팀 조회 (없으면 404)
2. `should_reset_budget()` 참이면 해당 팀 지출 전체 삭제 + `last_reset_date` 갱신 (자동 초기화)
3. `calculate_accumulated_budget()`로 누적 예산 계산
4. 현재 팀의 지출 목록으로 `total_spent`, `supply_amount_spent`, `vat_spent` 합산
5. `remaining_budget = accumulated_budget - total_spent`
6. `remaining_budget_without_vat = accumulated_budget - supply_amount_spent`
7. 팀원별 지출 합계(`member_expenses`)를 이름 기준으로 집계

### 8.5 Settings (`/api/settings`, `app/api/settings.py`)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/settings/{team_id}` | 팀의 `per_person_amount`/`budget_cycle` 조회 |
| PUT | `/api/settings/{team_id}` | 위 두 값 수정 |
| POST | `/api/settings/{team_id}/reset-budget` | 수동 예산 초기화 (해당 팀 지출 전체 삭제 + `last_reset_date` 갱신) |
| GET | `/api/settings/{team_id}/download-expenses` | 팀 지출 내역을 JSON 파일로 다운로드 |
| POST | `/api/settings/{team_id}/upload-expenses` | JSON 파일 업로드로 지출 내역 복구 |

**다운로드**: `data/expenses_{team_id}_{timestamp}.json` 임시 파일을 만들어 `FileResponse`로 반환(파일은 서버에 남는다 — 정리 로직 없음).

**업로드**: 업로드된 JSON이 배열이어야 하며, 각 항목의 `team_id`는 보안상 URL 파라미터 값으로 강제 덮어쓴 뒤 기존 해당 팀 지출을 전부 지우고 교체한다.

## 9. 화면 라우트 (`main.py`)

| Path | 템플릿 | 설명 |
|---|---|---|
| `GET /` | `index.html` | 시작 페이지 |
| `GET /login` | `login.html` | 팀/팀원 선택 로그인, 관리자 로그인 |
| `GET /dashboard` | `dashboard.html` | 대시보드, 지출 등록/조회 |
| `GET /api` | - | 헬스체크 성격의 JSON(`{"message": "BudgetPro API"}`) |

정적 파일은 `/static`에 마운트(`static/` 디렉토리), CORS는 `allow_origins=["*"]`로 전체 허용.

## 10. 알려진 제약 / 운영 시 유의사항

- 인증/인가가 사실상 없음 (6장). 팀 ID, 팀원 ID만 알면 누구나 API를 직접 호출해 데이터를 읽고 쓸 수 있다.
- 팀 삭제 시 팀원/지출 데이터가 함께 정리되지 않아 고아 레코드가 남을 수 있다.
- `save_teams`/`save_expenses`가 매 호출마다 테이블 전체를 지우고 다시 쓰는 방식이라, 동시 요청이 몰리면 경쟁 조건(lost update) 가능성이 있다. 트랜잭션 격리나 락은 별도로 구현되어 있지 않다.
- 지출 다운로드 시 생성되는 임시 JSON 파일(`data/expenses_*.json`)이 자동 삭제되지 않는다.
- CORS 전체 허용, UUID 기반 무검증 토큰 등은 개발/데모 목적의 단순화이며 운영 배포 전 보완이 필요하다.
