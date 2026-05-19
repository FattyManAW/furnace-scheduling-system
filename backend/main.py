"""
干式套管最佳化排爐系統 — FastAPI 主程式
前後端分離架構：此檔案只負責 API + CORS，前端由 Vite 獨立服務
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from database import engine, Base
from api import orders, molds, kilns, schedule, reports, process_steps

# ── 啟動時建立資料表 ────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI app ──────────────────────────────────────────────────────────
app = FastAPI(
    title="干式套管最佳化排爐系統 API",
    description="RESTful API — 訂單管理、模具庫存、干燥罐、排程優化、報表匯出",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

import os as _os
# ── CORS — 優先使用環境變數，開發 fallback 允許 localhost ──
_allowed = _os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed:
    _origins = [o.strip() for o in _allowed.split(",") if o.strip()]
else:
    _origins = [
        "http://localhost:5173", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由掛載 ──────────────────────────────────────────────────────────────
app.include_router(orders.router)
app.include_router(molds.router)
app.include_router(kilns.router)
app.include_router(schedule.router)
app.include_router(reports.router)
app.include_router(process_steps.router)


# ── 健康檢查 / 首頁 ──────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {
        "name": "干式套管最佳化排爐系統",
        "version": "2.0.0",
        "docs": "/docs",
        "api": "/openapi.json",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}



# ── 全域異常處理 ──────────────────────────────────────────────────────────────
from fastapi.requests import Request as _Request
from fastapi.responses import JSONResponse as _JSONResponse
from fastapi.exceptions import RequestValidationError as _RequestValidationError
from starlette.exceptions import HTTPException as _StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError as _SQLAlchemyError

@app.exception_handler(_StarletteHTTPException)
async def http_exc_handler(request: _Request, exc: _StarletteHTTPException):
    return _JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "http_exception"},
    )

@app.exception_handler(_RequestValidationError)
async def validation_exc_handler(request: _Request, exc: _RequestValidationError):
    return _JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "type": "validation_error"},
    )

@app.exception_handler(_SQLAlchemyError)
async def db_exc_handler(request: _Request, exc: _SQLAlchemyError):
    return _JSONResponse(
        status_code=500,
        content={"detail": "資料庫錯誤", "type": "database_error"},
    )

@app.exception_handler(Exception)
async def generic_exc_handler(request: _Request, exc: Exception):
    return _JSONResponse(
        status_code=500,
        content={"detail": f"內部伺服器錯誤: {exc!s}", "type": "internal_error"},
    )


# ── 執行 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8002))
    print(f"🔥 干式套管最佳化排爐系統 API")
    print(f"   http://localhost:{port}")
    print(f"   Swagger UI: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
