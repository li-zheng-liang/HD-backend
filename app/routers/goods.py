"""商品接口：列表（分页+搜索）、新增、修改、删除。

⚠️ 注意：SQL 里的 WHERE 条件用拼接（cond 变量），但拼接的只是固定的
"name LIKE ?" / "category LIKE ?" 这些模板片段，用户输入的值全部走
参数化查询（? 占位符 + params 列表），不存在 SQL 注入风险。
"""

from fastapi import APIRouter, Query

from app.database import get_db
from app.response import fail, ok
from app.schemas import GoodsIn, GoodsUpdate

router = APIRouter(tags=["商品"])


@router.get("/goods/list")
def goods_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    name: str = "",
    category: str = "",
):
    """商品列表：支持分页 + 按名称/分类模糊搜索。参数名与前端 GoodsQuery 一致。"""
    with get_db() as db:
        # 1. 动态拼接查询条件
        where, params = [], []
        if name:
            where.append("name LIKE ?")
            params.append(f"%{name}%")
        if category:
            where.append("category LIKE ?")
            params.append(f"%{category}%")
        cond = (" WHERE " + " AND ".join(where)) if where else ""

        # 2. 先查总数（分页必需）
        total = db.execute(f"SELECT COUNT(*) FROM goods{cond}", params).fetchone()[0]

        # 3. 再查当前页数据
        rows = db.execute(
            f"SELECT * FROM goods{cond} ORDER BY id LIMIT ? OFFSET ?",
            params + [pageSize, (page - 1) * pageSize],
        ).fetchall()

    return ok({"list": [dict(r) for r in rows], "total": total})


@router.post("/goods")
def add_goods(body: GoodsIn):
    """新增商品。mock 里 id 自增，这里由数据库 AUTOINCREMENT 自动生成。"""
    with get_db() as db:
        db.execute(
            "INSERT INTO goods (name, category, spec, unit, price, stock, status) "
            "VALUES (?,?,?,?,?,?,?)",
            (body.name, body.category, body.spec, body.unit, body.price, body.stock, body.status),
        )
    return ok()


@router.put("/goods")
def update_goods(body: GoodsUpdate):
    """修改商品：按 id 更新，商品不存在则返回 404。"""
    with get_db() as db:
        cur = db.execute(
            "UPDATE goods SET name=?, category=?, spec=?, unit=?, price=?, stock=?, status=? "
            "WHERE id=?",
            (body.name, body.category, body.spec, body.unit, body.price, body.stock, body.status, body.id),
        )
        if cur.rowcount == 0:
            return fail(404, f"商品 {body.id} 不存在")
    return ok()


@router.delete("/goods")
def delete_goods(id: int = Query(..., description="商品 id")):
    """删除商品：DELETE /api/goods?id=xx"""
    with get_db() as db:
        cur = db.execute("DELETE FROM goods WHERE id=?", (id,))
        if cur.rowcount == 0:
            return fail(404, f"商品 {id} 不存在")
    return ok()
