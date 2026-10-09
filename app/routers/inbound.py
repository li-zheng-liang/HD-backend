"""入库接口：列表 + 新增。

核心业务规则（与 mock 一致）：
- 生成单号 IN + 年月日 + 当日3位序号
- 金额 = 数量 × 单价
- ★ 入库后商品库存自动增加
"""

from datetime import datetime

from fastapi import APIRouter

from app.database import get_db, make_no
from app.response import fail, ok
from app.schemas import InboundIn

router = APIRouter(tags=["入库"])


@router.get("/inbound/list")
def inbound_list():
    """入库单列表：最新在前。"""
    with get_db() as db:
        rows = db.execute("SELECT * FROM inbound ORDER BY id DESC").fetchall()
    return ok({"list": [dict(r) for r in rows], "total": len(rows)})


@router.post("/inbound")
def add_inbound(body: InboundIn):
    """新增入库单：校验商品存在 → 生成单号 → 落库 → 商品库存联动增加。"""
    with get_db() as db:
        goods = db.execute("SELECT * FROM goods WHERE id=?", (body.goodsId,)).fetchone()
        if not goods:
            return fail(404, "商品不存在")

        no = make_no("IN", db, "inbound")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        amount = round(body.quantity * body.price, 2)

        db.execute(
            "INSERT INTO inbound (no, goods_id, goods_name, quantity, price, amount, remark, create_time) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (no, goods["id"], goods["name"], body.quantity, body.price, amount, body.remark, now),
        )
        # ★ 业务规则：商品库存联动增加
        db.execute("UPDATE goods SET stock = stock + ? WHERE id=?", (body.quantity, body.goodsId))

    return ok()
