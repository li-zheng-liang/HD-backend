"""数据库模块：使用 Python 自带的 sqlite3，不需要额外安装任何数据库服务。

设计要点：
1. 数据文件 mes.db 放在 HD 项目根目录，首次启动自动创建 —— 数据持久化，
   免费服务器重启后数据不会丢。
2. 每个请求单独开一个连接、用完即关（with get_db() as db），避免多线程
   共用同一个 sqlite 连接导致的报错。
3. with 块正常结束自动 commit，异常自动 rollback。
"""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

# 数据库文件位置：HD/mes.db（app/database.py 的上一级目录）
DB_PATH = Path(__file__).resolve().parent.parent / "mes.db"


def get_connection() -> sqlite3.Connection:
    """新建一个数据库连接。row_factory=Row 让查询结果可以用列名访问（row["name"]）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """上下文管理器：with get_db() as db: ... 结束时自动提交并关闭连接。"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """建表 + 写入初始演示数据。幂等操作：表已存在则不重建、已有数据则不重复插入。"""
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS goods (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                category TEXT NOT NULL,
                spec     TEXT DEFAULT '',
                unit     TEXT DEFAULT '',
                price    REAL NOT NULL,
                stock    INTEGER NOT NULL DEFAULT 0,
                status   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS inbound (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                no          TEXT NOT NULL,
                goods_id    INTEGER NOT NULL,
                goods_name  TEXT NOT NULL,
                quantity    INTEGER NOT NULL,
                price       REAL NOT NULL,
                amount      REAL NOT NULL,
                remark      TEXT DEFAULT '',
                create_time TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outbound (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                no          TEXT NOT NULL,
                goods_id    INTEGER NOT NULL,
                goods_name  TEXT NOT NULL,
                quantity    INTEGER NOT NULL,
                price       REAL NOT NULL,
                amount      REAL NOT NULL,
                remark      TEXT DEFAULT '',
                create_time TEXT NOT NULL
            );
            """
        )

        # ---- 初始商品数据（与前端 mock 一致），仅当表为空时写入 ----
        count = db.execute("SELECT COUNT(*) FROM goods").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO goods (name, category, spec, unit, price, stock, status) VALUES (?,?,?,?,?,?,?)",
                [
                    ("螺丝钉 M4", "标准件", "M4×20", "盒", 12.5, 320, 1),
                    ("轴承 6205", "传动件", "6205-2RS", "个", 18.0, 86, 1),
                    ("液压油 46#", "油品", "18L/桶", "桶", 268.0, 45, 1),
                    ("电缆 RVV 3×2.5", "电气", "100m/卷", "卷", 320.0, 12, 1),
                    ("焊条 E5015", "焊接", "Φ3.2", "kg", 8.6, 5, 0),
                ],
            )

        # ---- 初始出入库单据（日期用"今天"，保证报表"近7天趋势"有数据显示）----
        today = datetime.now()
        inbound_count = db.execute("SELECT COUNT(*) FROM inbound").fetchone()[0]
        if inbound_count == 0:
            db.execute(
                "INSERT INTO inbound (no, goods_id, goods_name, quantity, price, amount, remark, create_time) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (f"IN{today:%Y%m%d}001", 1, "螺丝钉 M4", 100, 12.5, 1250.0, "采购入库",
                 today.strftime("%Y-%m-%d %H:%M:%S")),
            )

        outbound_count = db.execute("SELECT COUNT(*) FROM outbound").fetchone()[0]
        if outbound_count == 0:
            db.execute(
                "INSERT INTO outbound (no, goods_id, goods_name, quantity, price, amount, remark, create_time) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (f"OUT{today:%Y%m%d}001", 2, "轴承 6205", 20, 18.0, 360.0, "车间领用",
                 today.strftime("%Y-%m-%d %H:%M:%S")),
            )


def make_no(prefix: str, db: sqlite3.Connection, table: str) -> str:
    """生成单号：IN/OUT + 年月日 + 3 位当日序号，例如 IN20261009002。

    :param prefix: 单号前缀，"IN" 或 "OUT"
    :param db: 数据库连接（用于查询当日已有单数）
    :param table: 表名 "inbound" 或 "outbound"
    """
    today = date.today().strftime("%Y%m%d")
    # 单号格式：前缀 + 8位日期 + 3位序号，所以日期是 no 的第 3~10 位
    seq = db.execute(
        f"SELECT COUNT(*) FROM {table} WHERE substr(no, 3, 8) = ?", (today,)
    ).fetchone()[0] + 1
    return f"{prefix}{today}{seq:03d}"
