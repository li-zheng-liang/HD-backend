"""FastAPI 应用入口。

本地启动：uvicorn app.main:app --reload --port 8000
线上启动：见 Procfile（uvicorn app.main:app --host 0.0.0.0 --port $PORT）
启动后访问 /docs 可查看全部接口的 Swagger 文档并在线测试。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.response import ok
from app.routers import auth, goods, inbound, outbound, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库（建表 + 种子数据），关闭时无需清理。"""
    init_db()
    yield


app = FastAPI(
    title="MES 后端 API",
    description="基于 mes 前端 mock 接口实现的 Python 后端（FastAPI + SQLite）",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 跨域：前端部署在别的域名（如 GitHub Pages / Netlify）时也能正常请求。
# 演示项目放开所有来源；正式项目建议改为具体的前端域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 所有业务接口统一挂在 /api 前缀下，与前端 axios baseURL 对应
app.include_router(auth.router, prefix="/api")
app.include_router(goods.router, prefix="/api")
app.include_router(inbound.router, prefix="/api")
app.include_router(outbound.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.get("/api/health")
def health():
    """健康检查：部署平台（Render）用它判断服务是否存活。"""
    return ok({"status": "up"})
