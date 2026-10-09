"""统一响应格式：与前端 mock（vite.config.ts）保持完全一致。

前端 axios 拦截器（src/utils/request.ts）的规则：
    res.code == 0  -> 成功，把 res.data 直接返回给页面
    res.code != 0  -> 失败，用 res.message 弹错误提示

⚠️ 重要：业务错误（登录失败、库存不足等）也必须返回 HTTP 200，
只通过 body 里的 code 区分成功失败。这样前端才能拿到 res.message 提示用户；
如果返回 HTTP 4xx/5xx，axios 会走 error 分支，用户只能看到
"Request failed with status code 400" 这种无用信息。
"""

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok") -> dict:
    """成功响应：{code: 0, data: ..., message: 'ok'}"""
    return {"code": 0, "data": data, "message": message}


def fail(code: int, message: str) -> JSONResponse:
    """业务失败响应：HTTP 200 + body 里 code != 0，message 给前端提示。"""
    return JSONResponse(
        status_code=200,
        content={"code": code, "data": None, "message": message},
    )
