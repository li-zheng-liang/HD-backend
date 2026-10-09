"""报表接口：分类库存汇总 + 近 7 天出入库趋势。

与 mock 的区别：mock 的趋势图是写死的假数据；这里从出入库单实时聚合，
数据真实、与页面操作联动。
"""

from datetime import date, timedelta

from fastapi import APIRouter

from app.database import get_db
from app.response import ok

router = APIRouter(tags=["报表"])


@router.get("/report/category-stock")
def category_stock():
    """各分类库存汇总：SELECT category, SUM(stock) 按分类分组求和。"""
    with get_db() as db:
        rows = db.execute(
            "SELECT category, SUM(stock) AS v FROM goods GROUP BY category ORDER BY v DESC"
        ).fetchall()
    return ok({"categories": [r["category"] for r in rows], "values": [r["v"] for r in rows]})


@router.get("/report/inout-trend")
def inout_trend():
    """近 7 天每天入库/出库数量合计，日期格式 MM-DD（与 mock 一致）。"""
    dates, inbound, outbound = [], [], []
    for i in range(6, -1, -1):  # 从 6 天前到今天
        d = date.today() - timedelta(days=i)
        prefix = d.strftime("%Y-%m-%d")  # create_time 以 "YYYY-MM-DD" 开头

        with get_db() as db:
            in_qty = db.execute(
                "SELECT COALESCE(SUM(quantity), 0) FROM inbound WHERE create_time LIKE ?",
                (prefix + "%",),
            ).fetchone()[0]
            out_qty = db.execute(
                "SELECT COALESCE(SUM(quantity), 0) FROM outbound WHERE create_time LIKE ?",
                (prefix + "%",),
            ).fetchone()[0]

        dates.append(d.strftime("%m-%d"))
        inbound.append(in_qty)
        outbound.append(out_qty)

    return ok({"dates": dates, "inbound": inbound, "outbound": outbound})
