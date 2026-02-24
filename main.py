from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.api import teams, members, expenses, auth, settings
import uvicorn
import sys

app = FastAPI(title="BudgetPro", version="1.0.0")

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(members.router, prefix="/api/members", tags=["members"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

# HTML 라우트
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api")
async def root():
    return {"message": "BudgetPro API"}

if __name__ == "__main__":
    # 커맨드 라인에서 포트 번호 받기 (기본값: 8000)
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                print("⚠️  포트 번호는 1-65535 사이여야 합니다. 기본 포트 8000을 사용합니다.")
                port = 8000
        except ValueError:
            print("⚠️  올바른 포트 번호를 입력하세요. 기본 포트 8000을 사용합니다.")
            port = 8000
    
    print(f"🚀 BudgetPro 서버를 포트 {port}에서 시작합니다...")
    print(f"📍 http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
