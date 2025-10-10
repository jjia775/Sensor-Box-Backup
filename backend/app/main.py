from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sensors, ingest, readings, register, auth, analytics, diseases
import os
from starlette.middleware.sessions import SessionMiddleware
app = FastAPI()
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 你的前端地址
    allow_credentials=True,  # 关键：允许携带 Cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key="please-change-me",  # 换成你的随机长字符串
    session_cookie="sid",           # 可选：自定义 cookie 名
    same_site="lax",                # 前后端同域/同站推荐 Lax；跨站可用 "none" + HTTPS
    https_only=False,               # 生产环境建议 True（仅 HTTPS 传输）
)
app.include_router(sensors.router)
app.include_router(ingest.router)
app.include_router(readings.router)

app.include_router(diseases.router)

app.include_router(register.router)

app.include_router(analytics.router)

# app.include_router(auth_router)
@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)