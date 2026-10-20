"""订单模块接口封装：创建 / 列表 / 详情 / 取消

登录态设计：构造 OrderApi 时注入 token（由 conftest 的登录 fixture 提供），
用例层不再手动拼 Authorization 头。
"""
from api.base_api import BaseApi


class OrderApi(BaseApi):

    def __init__(self, token: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.token = token

    def _auth_headers(self) -> dict:
        """token 为空时不携带 Authorization 头，让服务端返回 401 ——
        这是鉴权用例的测试目标，不能在客户端提前拦截"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def create(self, goods_id: str, quantity: int = 1):
        """POST /api/order/create"""
        return self.post(
            "/api/order/create",
            json={"goods_id": goods_id, "quantity": quantity},
            headers=self._auth_headers(),
        )

    def list_orders(self):
        """GET /api/order/list"""
        return self.get("/api/order/list", headers=self._auth_headers())

    def detail(self, order_id: str):
        """GET /api/order/{order_id}"""
        return self.get(f"/api/order/{order_id}", headers=self._auth_headers())

    def cancel(self, order_id: str):
        """PUT /api/order/{order_id}/cancel"""
        return self.put(f"/api/order/{order_id}/cancel", headers=self._auth_headers())
