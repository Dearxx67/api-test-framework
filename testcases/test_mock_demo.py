"""Mock 依赖隔离演示用例（responses 库）

业务场景：下单成功后，我方系统需调用【第三方物流 API】创建运单。
第三方服务的测试困境：
1. 测试环境不可用 / 沙箱环境不稳定
2. 调用有配额、有费用
3. 超时、宕机等异常场景无法按需复现

Mock 方案：responses 在 HTTP 层拦截 requests 请求并返回预置响应，
用例不真正出网 —— 依赖隔离 + 异常场景可控。
"""
import allure
import pytest
import requests
import responses

from utils.data_loader import load_yaml

order_data = load_yaml("order_data.yaml")

LOGISTICS_URL = "https://logistics.example.com/api/shipping"


@allure.epic("电商系统接口自动化测试")
@allure.feature("第三方依赖 Mock")
class TestMockLogistics:

    @allure.story("Mock 物流接口")
    @allure.title("Mock 第三方物流接口成功响应，业务链路正常拿到运单号")
    @pytest.mark.regression
    @pytest.mark.mock
    @responses.activate  # 激活拦截：本用例内所有 requests 请求都不会真正出网
    def test_mock_logistics_success(self):
        # 预置第三方"成功"响应
        responses.post(
            LOGISTICS_URL,
            json={"code": 0, "msg": "ok", "data": {"tracking_no": "SF1234567890"}},
            status=200,
        )

        # 业务代码调用第三方物流接口（这里模拟下单后创建运单的动作）
        resp = requests.post(LOGISTICS_URL, json={"order_id": "demo_order"}, timeout=5)

        assert resp.status_code == 200
        assert resp.json()["data"]["tracking_no"] == "SF1234567890"

    @allure.story("Mock 物流接口")
    @allure.title("Mock 第三方物流接口超时，验证我方超时异常处理")
    @pytest.mark.regression
    @pytest.mark.mock
    @pytest.mark.negative
    @responses.activate
    def test_mock_logistics_timeout(self):
        # 真实环境里第三方超时极难复现，mock 一行搞定
        responses.post(LOGISTICS_URL, body=requests.exceptions.ConnectTimeout())

        with pytest.raises(requests.exceptions.ConnectTimeout):
            requests.post(LOGISTICS_URL, json={"order_id": "demo_order"}, timeout=5)

    @allure.story("Mock 物流接口")
    @allure.title("Mock 第三方物流接口 500，验证降级逻辑")
    @pytest.mark.regression
    @pytest.mark.mock
    @pytest.mark.negative
    @responses.activate
    def test_mock_logistics_server_error(self):
        responses.post(LOGISTICS_URL, json={"error": "internal"}, status=500)

        resp = requests.post(LOGISTICS_URL, json={"order_id": "demo_order"}, timeout=5)

        assert resp.status_code == 500
        # 实际项目中此处应断言我方系统的降级/重试/告警逻辑

    @allure.story("Mock 被测系统响应")
    @allure.title("Mock 登录接口返回 500，验证框架异常捕获不静默吞错")
    @pytest.mark.regression
    @pytest.mark.mock
    @pytest.mark.negative
    @responses.activate
    def test_mock_login_server_error(self, user_api):
        """mock 被测系统本身的异常响应：服务端 500 这类场景在真实环境
        很难按需触发，用 mock 保证异常分支被覆盖"""
        responses.post(
            f"{user_api.base_url}/api/user/login",
            json={"detail": "internal server error"},
            status=500,
        )

        resp = user_api.login("anyone", "whatever")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "internal server error"
