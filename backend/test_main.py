"""
测试主程序（使用SQLite）
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from test_database import init_db, get_db, User, Analysis, ShareLink
from test_config import settings
from test_routers import auth
from test_routers import analyses
from test_routers import files
from test_routers import shares

app = FastAPI(title="朋友圈分析API (测试模式)", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(files.router)
app.include_router(shares.router)

# 开发模式：把未捕获异常返回到前端，方便排错（仅测试模式使用）
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {str(exc)}",
            "trace": traceback.format_exc().splitlines()[-20:],  # 只回传最后20行，避免太长
        },
    )

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ 数据库初始化完成！")

@app.get("/")
async def root():
    return {
        "message": "朋友圈分析API (测试模式)",
        "version": "1.0.0",
        "database": "SQLite",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    try:
        from test_auth import _prehash_if_needed  # type: ignore
        prehash_ok = _prehash_if_needed("a" * 100).startswith("sha256:")
    except Exception:
        prehash_ok = False
    return {"status": "ok", "auth_prehash": prehash_ok}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 后端服务启动中...")
    print("📍 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("💾 数据库: SQLite (test.db)")
    print("="*50 + "\n")
    # 注意：使用 python 直接运行时，不要启用 reload=True（需要 import string 才支持 reload）
    # 如需热更新，请使用：
    # uvicorn test_main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
