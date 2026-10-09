"""登录接口：POST /api/login

账号密码校验。前端只把 token 存 localStorage、不在请求头里携带，
所以这里无需做鉴权拦截（与 mock 行为一致，保持简单）。
"""

import secrets

from fastapi import APIRouter

from app.response import fail, ok
from app.schemas import LoginIn

router = APIRouter(tags=["登录"])


@router.post("/login")
def login(body: LoginIn):
    """与 mock 相同的账号密码：admin / 123456"""
    if body.username == "admin" and body.password == "123456":
        # secrets.token_hex 生成随机 token，比 mock 的固定值更真实
        return ok({"token": secrets.token_hex(16), "userName": "admin"})
    return fail(401, "用户名或密码错误")
