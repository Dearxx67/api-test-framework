"""用户模块接口测试用例

覆盖场景：
1. 注册：正向注册、重复用户名注册
2. 登录：正确账密（数据驱动：错误密码 / 不存在用户）
3. 用户信息查询：有效 token / 无 token / 伪造 token
"""
import random

import allure
import pytest

from utils.data_loader import load_yaml

user_data = load_yaml("user_data.yaml")


@allure.epic("电商系统接口自动化测试")
@allure.feature("用户模块")
class TestRegister:

    @allure.story("注册")
    @allure.title("合法随机数据注册成功，且注册后可正常登录")
    @pytest.mark.smoke
    @pytest.mark.user
    def test_register_ok(self, user_api, registered_user):
        """registered_user fixture 已完成注册，本用例验证注册结果真实可用（业务闭环）"""
        with allure.step("step1: 使用新注册账号登录"):
            resp = user_api.login(
                registered_user["username"], registered_user["password"]
            )
        with allure.step("step2: 校验登录响应"):
            assert resp.status_code == 200
            body = resp.json()
            assert body["code"] == 0
            assert body["data"]["token"], "登录响应应包含 token"

    @allure.story("注册")
    @allure.title("重复用户名注册，返回 400 及明确错误信息")
    @pytest.mark.regression
    @pytest.mark.user
    @pytest.mark.negative
    def test_register_duplicate(self, user_api):
        data = user_data["register"]["duplicate"]
        username = f"{data['username_prefix']}_{random.randint(10000, 99999)}"

        with allure.step("step1: 首次注册应成功"):
            first = user_api.register(username, data["password"])
            assert first.status_code == 200

        with allure.step("step2: 重复注册应失败"):
            second = user_api.register(username, data["password"])
            assert second.status_code == data["expected_status"]
            assert data["expected_detail_contains"] in second.json()["detail"]


@allure.feature("用户模块")
class TestLogin:

    @allure.story("登录")
    @allure.title("登录用例（数据驱动：正确账密/错误密码/用户不存在）")
    @pytest.mark.regression
    @pytest.mark.user
    @pytest.mark.parametrize(
        "case_data", user_data["login"]["cases"], ids=lambda c: c["case"]
    )
    def test_login(self, user_api, registered_user, case_data):
        """数据驱动：YAML 中未指定的字段自动使用 fixture 的合法账号"""
        username = case_data.get("username", registered_user["username"])
        password = case_data.get("password", registered_user["password"])

        resp = user_api.login(username, password)
        assert resp.status_code == case_data["expected_status"]

        if resp.status_code == 200:
            assert resp.json()["code"] == case_data["expected_code"]
        else:
            assert case_data["expected_detail_contains"] in resp.json()["detail"]


@allure.feature("用户模块")
class TestUserInfo:

    @allure.story("用户信息查询")
    @allure.title("携带有效 token 查询用户信息成功")
    @pytest.mark.smoke
    @pytest.mark.user
    def test_info_ok(self, user_api, login_token, registered_user):
        resp = user_api.get_info(login_token)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == registered_user["username"]

    @allure.story("用户信息查询")
    @allure.title("不带 token 查询，返回 401")
    @pytest.mark.regression
    @pytest.mark.user
    @pytest.mark.negative
    def test_info_no_token(self, user_api):
        resp = user_api.get_info(token="")  # 不携带 Authorization 头
        assert resp.status_code == 401

    @allure.story("用户信息查询")
    @allure.title("携带伪造 token 查询，返回 401")
    @pytest.mark.regression
    @pytest.mark.user
    @pytest.mark.negative
    def test_info_invalid_token(self, user_api):
        resp = user_api.get_info(token="fake_token_123456")
        assert resp.status_code == 401
        assert "token" in resp.json()["detail"]
