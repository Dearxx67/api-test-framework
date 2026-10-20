"""模拟后端服务：电商用户/订单系统（FastAPI 实现）

用途：
1. 作为接口自动化测试的被测服务，使项目可独立运行、不依赖外部环境
2. 体现测试开发能力：自己能开发服务、模拟依赖（对应 JD"接口 mock/测试工具开发"）

启动：.venv/Scripts/python.exe -m uvicorn mock_server.app:app --port 8000
接口文档（Swagger 自动生成）：http://127.0.0.1:8000/docs
"""
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock 电商后端", version="1.0.0")

# ---------- 内存"数据库"（重启即重置，天然保证用例可重复执行） ----------
USERS = {}   # username -> user dict
TOKENS = {}  # token -> username
ORDERS = {}  # order_id -> order dict
GOODS = {
    "1001": {"name": "机械键盘", "price": 299.0, "stock": 100},
    "1002": {"name": "无线鼠标", "price": 99.0, "stock": 5},
    "1003": {"name": "4K显示器", "price": 1999.0, "stock": 0},
}


# ---------- 请求体模型 ----------
class RegisterReq(BaseModel):
    username: str
    password: str
    email: str = ""


class LoginReq(BaseModel):
    username: str
    password: str


class CreateOrderReq(BaseModel):
    goods_id: str
    quantity: int = 1


def get_current_user(authorization: str = Header(default="")) -> str:
    """从请求头 Authorization 解析 Bearer token，校验登录态"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录或 token 格式错误")
    username = TOKENS.get(authorization[7:])
    if not username:
        raise HTTPException(401, "token 无效或已过期")
    return username


# ---------- 健康检查 ----------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- 用户模块 ----------
@app.post("/api/user/register")
def register(req: RegisterReq):
    if not req.username.strip() or not req.password.strip():
        raise HTTPException(400, "用户名和密码不能为空")
    if req.username in USERS:
        raise HTTPException(400, f"用户名 {req.username} 已存在")
    USERS[req.username] = {
        "username": req.username,
        "password": req.password,
        "email": req.email,
    }
    return {"code": 0, "msg": "注册成功", "data": {"username": req.username}}


@app.post("/api/user/login")
def login(req: LoginReq):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(401, "用户名或密码错误")
    token = uuid.uuid4().hex
    TOKENS[token] = req.username
    return {"code": 0, "msg": "登录成功", "data": {"token": token}}


@app.get("/api/user/info")
def user_info(authorization: str = Header(default="")):
    username = get_current_user(authorization)
    user = USERS[username]
    return {
        "code": 0,
        "msg": "ok",
        "data": {"username": user["username"], "email": user["email"]},
    }


# ---------- 订单模块 ----------
@app.post("/api/order/create")
def create_order(req: CreateOrderReq, authorization: str = Header(default="")):
    username = get_current_user(authorization)

    goods = GOODS.get(req.goods_id)
    if not goods:
        raise HTTPException(400, f"商品 {req.goods_id} 不存在")
    if req.quantity < 1:
        raise HTTPException(400, "购买数量至少为 1")
    if goods["stock"] < req.quantity:
        raise HTTPException(400, "库存不足")

    goods["stock"] -= req.quantity
    order_id = uuid.uuid4().hex[:8]
    ORDERS[order_id] = {
        "order_id": order_id,
        "username": username,
        "goods_id": req.goods_id,
        "goods_name": goods["name"],
        "quantity": req.quantity,
        "total_price": round(goods["price"] * req.quantity, 2),
        "status": "pending",
    }
    return {"code": 0, "msg": "下单成功", "data": ORDERS[order_id]}


@app.get("/api/order/list")
def order_list(authorization: str = Header(default="")):
    username = get_current_user(authorization)
    my_orders = [o for o in ORDERS.values() if o["username"] == username]
    return {"code": 0, "msg": "ok", "data": {"total": len(my_orders), "items": my_orders}}


@app.get("/api/order/{order_id}")
def order_detail(order_id: str, authorization: str = Header(default="")):
    get_current_user(authorization)
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(404, f"订单 {order_id} 不存在")
    return {"code": 0, "msg": "ok", "data": order}


@app.put("/api/order/{order_id}/cancel")
def cancel_order(order_id: str, authorization: str = Header(default="")):
    username = get_current_user(authorization)
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(404, f"订单 {order_id} 不存在")
    if order["username"] != username:
        raise HTTPException(403, "不能取消他人订单")
    if order["status"] != "pending":
        raise HTTPException(400, f"订单状态为 {order['status']}，无法取消")

    order["status"] = "cancelled"
    GOODS[order["goods_id"]]["stock"] += order["quantity"]  # 取消订单回滚库存
    return {"code": 0, "msg": "取消成功", "data": order}
