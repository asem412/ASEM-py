"""
FastAPIメインアプリケーション
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import employees, takings, reports
from app.database import engine, Base

# テーブル作成（開発用）
# 本番ではalembicを使用
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="有給管理システム",
    description="従業員の有給休暇を管理するシステム",
    version="1.0.0"
)

# 静的ファイル
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレート
templates = Jinja2Templates(directory="app/templates")

# ルーター登録
app.include_router(employees.router)
app.include_router(takings.router)
app.include_router(reports.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ"""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
