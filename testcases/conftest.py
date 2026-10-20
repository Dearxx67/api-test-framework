"""全局 fixture：API 实例管理 + 测试账号隔离

fixture 作用域设计（面试考点）：
- user_api  : session 级，整个测试会话复用同一实例（底层 requests.Session 连接复用）
- registered_user : function 级，每条用例注册独立随机账号，用例间零依赖、可重复执行
- login_token / order_api : 依赖注入，自动携带登录态
"""
import pytest

from api.order_api import OrderApi
from api.user_api import UserApi
from utils.data_factory import gen_user


@pytest.fixture(scope="session")
def user_api() -> UserApi:
    return UserApi()


@pytest.fixture(scope="session")
def _shared_password() -> str:
    """所有自动生成账号使用统一密码，便于排查时手工登录复现"""
    return "Auto@Test123"


@pytest.fixture()
def registered_user(user_api, _shared_password):
    """每条用例注册一个随机新用户，返回 {username, password}"""
    user = gen_user()  # Faker 数据工厂生成随机账号
    user["password"] = _shared_password  # 统一密码便于排查复现
    resp = user_api.register(user["username"], user["password"], email=user["email"])
    assert resp.status_code == 200, f"前置注册失败: {resp.status_code} {resp.text}"
    return {"username": user["username"], "password": user["password"]}


@pytest.fixture()
def login_token(user_api, registered_user):
    """登录并返回 token，供需要登录态的用例/接口使用"""
    resp = user_api.login(
        registered_user["username"], registered_user["password"]
    )
    assert resp.status_code == 200, f"前置登录失败: {resp.status_code} {resp.text}"
    return resp.json()["data"]["token"]


@pytest.fixture()
def order_api(login_token) -> OrderApi:
    """带登录态的订单 API 实例"""
    return OrderApi(token=login_token)
