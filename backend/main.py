"""
朋友圈截图分析交友助手 - 后端主程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, analyses, files, shares
from database import init_db

app = FastAPI(title="朋友圈分析API", version="1.0.0")

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

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "朋友圈分析API", "version": "1.0.0"}

@app.get("/health")
async def health():
    try:
        from auth import _prehash_if_needed  # type: ignore
        prehash_ok = _prehash_if_needed("a" * 100).startswith("sha256:")
    except Exception:
        prehash_ok = False
    return {"status": "ok", "auth_prehash": prehash_ok}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
