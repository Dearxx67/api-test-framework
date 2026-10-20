"""用户模块接口封装：注册 / 登录 / 查询用户信息"""
from api.base_api import BaseApi


class UserApi(BaseApi):

    def register(self, username: str, password: str, email: str = ""):
        """POST /api/user/register"""
        return self.post(
            "/api/user/register",
            json={"username": username, "password": password, "email": email},
        )

    def login(self, username: str, password: str):
        """POST /api/user/login，成功后返回 token"""
        return self.post(
            "/api/user/login",
            json={"username": username, "password": password},
        )

    def get_info(self, token: str):
        """GET /api/user/info，需携带 Bearer token"""
        return self.get(
            "/api/user/info",
            headers={"Authorization": f"Bearer {token}"},
        )
