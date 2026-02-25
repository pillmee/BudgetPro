# BudgetPro

팀 예산을 관리하는 FastAPI 기반 웹 애플리케이션입니다.  
팀/팀원 관리, 지출 등록, 대시보드 조회, 설정(예산 주기/초기화/백업 복구)을 제공합니다.

## 주요 기능

- 팀 CRUD (생성/조회/수정/삭제)
- 팀원 CRUD (생성/조회/수정/삭제)
- 팀 + 팀원 선택 로그인
- 대시보드 예산/지출 집계
- 지출 등록 시 공급가액/부가세(10%) 자동 계산
- 예산 주기 설정: 월/분기/반기/연
- 팀별 지출 JSON 다운로드/업로드
- JSON 파일 기반 저장(`data/teams.json`, `data/expenses.json`)

## 빠른 시작

### 1) 설치

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

의존성 설치:

```bash
pip install -r requirements.txt
```

### 2) 실행

```bash
python main.py
```

기본 포트는 `8000`이며, 포트를 지정하려면:

```bash
python main.py 8080
```

## 접속 주소

- 웹 시작 페이지: `http://localhost:8000/`
- 로그인 페이지: `http://localhost:8000/login`
- 대시보드 페이지: `http://localhost:8000/dashboard`
- API 문서(Swagger): `http://localhost:8000/docs`
- API 문서(ReDoc): `http://localhost:8000/redoc`

## API 요약

### Teams

- `GET /api/teams`
- `GET /api/teams/{team_id}`
- `POST /api/teams`
- `PUT /api/teams/{team_id}`
- `DELETE /api/teams/{team_id}`

### Members

- `GET /api/members/{team_id}`
- `GET /api/members/{team_id}/{member_id}`
- `POST /api/members/{team_id}`
- `PUT /api/members/{team_id}/{member_id}`
- `DELETE /api/members/{team_id}/{member_id}`

### Expenses

- `GET /api/expenses?team_id={team_id}`
- `GET /api/expenses/{expense_id}`
- `POST /api/expenses`
- `DELETE /api/expenses/{expense_id}`

### Auth / Dashboard

- `POST /api/auth/login`
- `GET /api/auth/dashboard/{team_id}`

### Settings

- `GET /api/settings/{team_id}`
- `PUT /api/settings/{team_id}`
- `POST /api/settings/{team_id}/reset-budget`
- `GET /api/settings/{team_id}/download-expenses`
- `POST /api/settings/{team_id}/upload-expenses`

## 핵심 계산 규칙

- 누적 예산: `인별 할당액 × 팀원 수 × (경과 개월 + 1)`
- 공급가액: `int(총액 / 1.1)`
- 부가세: `총액 - 공급가액`
- 잔여 예산: `누적 예산 - 총 지출`
- 부가세 제외 잔여 예산: `누적 예산 - 공급가액 합계`

## 프로젝트 구조

```text
BudgetPro/
├─ main.py
├─ requirements.txt
├─ app/
│  ├─ models.py
│  ├─ utils.py
│  ├─ budget_calculator.py
│  └─ api/
│     ├─ teams.py
│     ├─ members.py
│     ├─ expenses.py
│     ├─ auth.py
│     └─ settings.py
├─ templates/
├─ static/
└─ data/
```

## 운영 시 참고

- 현재 저장소는 JSON 파일 저장 방식입니다. 운영 환경에서는 DB 사용을 권장합니다.
- 인증 토큰은 UUID 기반의 단순 구현입니다. 운영 환경에서는 JWT 등으로 교체하세요.
- CORS가 전체 허용(`*`)으로 설정되어 있으므로 운영 환경에서는 제한이 필요합니다.
