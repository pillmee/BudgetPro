# BudgetPro API

FastAPI를 사용한 팀 예산 관리 시스템

## 기능

- 다중 팀 관리 (추가, 수정, 삭제)
- 팀원 관리 (추가, 수정, 삭제)
- 팀/팀원 선택 로그인
- 예산 자동 누적 (인별 할당액 × 팀원 수 × 경과 월)
- 지출 관리 (공급가액 + 부가세 10% 자동 계산)
- 지출 카테고리: 회식, 음료, 사무용품, 기타
- 예산 초기화 주기: 월별, 분기별, 반기별, 연도별
- JSON 파일 기반 데이터 관리

## 설치

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
# 개발 서버 실행
python main.py

# 또는
uvicorn main:app --reload
```

API는 http://localhost:8000 에서 실행됩니다.

API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.

## 프로젝트 구조

```
BudgetPro/
├── main.py                 # FastAPI 애플리케이션 진입점
├── requirements.txt        # 의존성 패키지
├── README.md              # 프로젝트 문서
├── instruction.md         # 구현 명세서
├── data/                  # JSON 데이터 파일 (자동 생성)
│   ├── teams.json        # 팀 및 팀원 정보
│   └── expenses.json     # 지출 내역
└── app/
    ├── __init__.py
    ├── models.py          # Pydantic 모델
    ├── utils.py           # 유틸리티 함수
    ├── budget_calculator.py  # 예산 계산 로직
    └── api/
        ├── __init__.py
        ├── teams.py       # 팀 관리 API
        ├── members.py     # 팀원 관리 API
        ├── expenses.py    # 지출 관리 API
        ├── auth.py        # 로그인 및 대시보드 API
        └── settings.py    # 설정 관리 API
```

## API 엔드포인트

### 팀 관리
- `GET /api/teams` - 모든 팀 조회
- `GET /api/teams/{team_id}` - 특정 팀 조회
- `POST /api/teams` - 팀 생성
- `PUT /api/teams/{team_id}` - 팀 수정
- `DELETE /api/teams/{team_id}` - 팀 삭제

### 팀원 관리
- `GET /api/members/{team_id}` - 팀의 모든 팀원 조회
- `GET /api/members/{team_id}/{member_id}` - 특정 팀원 조회
- `POST /api/members/{team_id}` - 팀원 생성
- `PUT /api/members/{team_id}/{member_id}` - 팀원 수정
- `DELETE /api/members/{team_id}/{member_id}` - 팀원 삭제

### 지출 관리
- `GET /api/expenses?team_id={team_id}` - 지출 내역 조회
- `GET /api/expenses/{expense_id}` - 특정 지출 조회
- `POST /api/expenses` - 지출 생성
- `DELETE /api/expenses/{expense_id}` - 지출 삭제

### 인증 및 대시보드
- `POST /api/auth/login` - 로그인
- `GET /api/auth/dashboard/{team_id}` - 대시보드 데이터 조회

### 설정
- `GET /api/settings/{team_id}` - 팀 설정 조회
- `PUT /api/settings/{team_id}` - 팀 설정 수정
- `POST /api/settings/{team_id}/reset-budget` - 예산 초기화
- `GET /api/settings/{team_id}/download-expenses` - 지출 데이터 다운로드
- `POST /api/settings/{team_id}/upload-expenses` - 지출 데이터 업로드

## 데이터 모델

### 팀 (Team)
- id: 팀 ID
- name: 팀 이름
- per_person_amount: 인별 할당액
- budget_cycle: 예산 초기화 주기
- members: 팀원 목록
- last_reset_date: 마지막 예산 초기화 날짜

### 팀원 (Member)
- id: 팀원 ID
- name: 팀원 이름
- created_at: 생성일시

### 지출 (Expense)
- id: 지출 ID
- team_id: 팀 ID
- member_id: 팀원 ID
- member_name: 팀원 이름
- category: 지출 카테고리
- description: 지출 내용
- supply_amount: 공급가액
- vat: 부가세
- total_amount: 총 지출액
- created_at: 생성일시

## 예산 계산 로직

- **누적 예산**: `인별 할당액 × 팀원 수 × 경과 월수`
- **공급가액**: `총 지출액 ÷ 1.1` (소수점 이하 버림)
- **부가세**: `총 지출액 - 공급가액`
- **잔여 예산**: `누적 예산 - 총 지출액`
- **잔여 예산(부가세 제외)**: `누적 예산 - 공급가액`

## 주의사항

- 데이터는 JSON 파일로 저장되므로 프로덕션 환경에서는 데이터베이스 사용을 권장합니다.
- 인증 토큰은 간단한 UUID로 구현되어 있으며, 프로덕션에서는 JWT 등을 사용해야 합니다.
- CORS는 모든 origin을 허용하도록 설정되어 있으며, 프로덕션에서는 적절히 제한해야 합니다.
