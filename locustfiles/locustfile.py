"""Locust 压测脚本：电商用户/订单接口混合场景压测

设计要点（面试考点）：
1. 行为建模：每个虚拟用户先注册+登录获取 token，再按权重执行
   浏览(3) : 下单(2) : 查单(1) —— 模拟真实用户的浏览远多于下单
2. name 参数：把带动态参数的 URL 聚合成一条统计（否则统计被拆散）
3. wait_time：请求间隔 0.5~1.5s 模拟真人节奏，压测数据才有参考价值
4. headless + csv：无界面模式输出 CSV，方便 CI 归档与分析

运行方式（本机快速压测演示）：
  .venv/Scripts/python.exe -m locust -f locustfiles/locustfile.py \
      --host http://127.0.0.1:8000 -u 20 -r 2 -t 15s --headless \
      --csv reports/locust_stats --only-summary
"""
from locust import HttpUser, between, task

from utils.data_factory import gen_user


class ApiUser(HttpUser):
    """一个 ApiUser 实例 = 一个并发虚拟用户"""

    wait_time = between(0.5, 1.5)  # 模拟真人操作间隔

    def on_start(self):
        """每个虚拟用户启动时执行一次：注册新账号并登录拿 token"""
        user = gen_user()
        self.client.post("/api/user/register", json=user, name="POST /api/user/register")
        resp = self.client.post(
            "/api/user/login",
            json={"username": user["username"], "password": user["password"]},
            name="POST /api/user/login",
        )
        data = (resp.json() or {}).get("data") or {}
        self.token = data.get("token", "")

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def browse_user_info(self):
        """浏览：查询个人信息（权重 3，模拟高频读操作）"""
        self.client.get(
            "/api/user/info",
            headers=self._auth(),
            name="GET /api/user/info",
        )

    @task(2)
    def create_order(self):
        """下单：创建订单（权重 2，写操作）"""
        self.client.post(
            "/api/order/create",
            json={"goods_id": "1001", "quantity": 1},
            headers=self._auth(),
            name="POST /api/order/create",
        )

    @task(1)
    def view_order_list(self):
        """查单：订单列表（权重 1）"""
        self.client.get(
            "/api/order/list",
            headers=self._auth(),
            name="GET /api/order/list",
        )
