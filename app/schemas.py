"""Pydantic 请求体模型：自动做参数校验 + 生成 /docs 接口文档。

前端传的字段是驼峰命名（goodsId / goodsName / createTime），
Pydantic 直接用同样的字段名，避免前后端字段不一致。
"""

from pydantic import BaseModel, Field


# ---------- 登录 ----------
class LoginIn(BaseModel):
    username: str
    password: str


# ---------- 商品 ----------
class GoodsIn(BaseModel):
    name: str
    category: str
    spec: str = ""
    unit: str = ""
    price: float = Field(ge=0, description="单价，不能为负")
    stock: int = Field(ge=0, description="库存，不能为负")
    status: int = Field(1, description="1=正常 0=停用")


class GoodsUpdate(GoodsIn):
    id: int  # 修改时必须带上 id


# ---------- 入库 ----------
class InboundIn(BaseModel):
    goodsId: int
    quantity: int = Field(gt=0, description="入库数量，必须大于 0")
    price: float = Field(ge=0)
    remark: str = ""


# ---------- 出库 ----------
class OutboundIn(BaseModel):
    goodsId: int
    quantity: int = Field(gt=0)
    price: float = Field(ge=0)
    remark: str = ""


class OutboundEdit(BaseModel):
    id: int  # 出库单 id
    goodsId: int
    quantity: int = Field(gt=0)
    price: float = Field(ge=0)
    remark: str = ""
