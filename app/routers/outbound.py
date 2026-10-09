"""出库接口：列表、新增、修改。

核心业务规则（与 mock 一致）：
- ★ 出库数量不能超过当前库存，否则返回 400 + 具体剩余量提示
- 出库后商品库存自动扣减
- 修改出库单：先把旧单占用的库存"还回去"，再按新数量重新扣减
  （mock 里 edit 不调整库存属于 bug，这里做了正确实现）
"""

from datetime import datetime

from fastapi import APIRouter

from app.database import get_db, make_no
from app.response import fail, ok
from app.schemas import OutboundEdit, OutboundIn

router = APIRouter(tags=["出库"])


@router.get("/outbound/list")
def outbound_list():
    """出库单列表：最新在前。"""
    with get_db() as db:
        rows = db.execute("SELECT * FROM outbound ORDER BY id DESC").fetchall()
    return ok({"list": [dict(r) for r in rows], "total": len(rows)})


@router.post("/outbound")
def add_outbound(body: OutboundIn):
    """新增出库单：校验商品存在 + 库存充足 → 生成单号 → 落库 → 库存扣减。"""
    with get_db() as db:
        goods = db.execute("SELECT * FROM goods WHERE id=?", (body.goodsId,)).fetchone()
        if not goods:
            return fail(404, "商品不存在")

        # ★ 核心业务校验：库存不足直接拒绝
        if goods["stock"] < body.quantity:
            return fail(400, f"库存不足，当前仅剩 {goods['stock']} {goods['unit']}")

        no = make_no("OUT", db, "outbound")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        amount = round(body.quantity * body.price, 2)

        db.execute(
            "INSERT INTO outbound (no, goods_id, goods_name, quantity, price, amount, remark, create_time) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (no, goods["id"], goods["name"], body.quantity, body.price, amount, body.remark, now),
        )
        # ★ 库存联动扣减
        db.execute("UPDATE goods SET stock = stock - ? WHERE id=?", (body.quantity, body.goodsId))

    return ok()


@router.post("/outbound/edit")
def edit_outbound(body: OutboundEdit):
    """修改出库单。

    正确做法：先把旧单占用的库存加回商品，再按新数量扣减，
    并校验"加回后"的库存是否够新数量。
    注意：所有校验都在修改之前完成，避免校验失败时事务把中间改动提交掉。
    """
    with get_db() as db:
        old = db.execute("SELECT * FROM outbound WHERE id=?", (body.id,)).fetchone()
        if not old:
            return fail(404, f"出库单 {body.id} 不存在")

        goods = db.execute("SELECT * FROM goods WHERE id=?", (body.goodsId,)).fetchone()
        if not goods:
            return fail(404, "商品不存在")

        # 校验：旧单归还后的库存 = goods.stock + old.quantity，必须 ≥ 新数量
        restored_stock = goods["stock"] + old["quantity"]
        if restored_stock < body.quantity:
            return fail(400, f"库存不足，当前仅剩 {restored_stock} {goods['unit']}")

        # 校验通过，开始修改
        db.execute("UPDATE goods SET stock = stock + ? WHERE id=?", (old["quantity"], old["goods_id"]))  # 归还旧占用
        db.execute("UPDATE goods SET stock = stock - ? WHERE id=?", (body.quantity, body.goodsId))       # 扣减新数量

        amount = round(body.quantity * body.price, 2)
        db.execute(
            "UPDATE outbound SET goods_id=?, goods_name=?, quantity=?, price=?, amount=?, remark=? WHERE id=?",
            (body.goodsId, goods["name"], body.quantity, body.price, amount, body.remark, body.id),
        )

    return ok()
