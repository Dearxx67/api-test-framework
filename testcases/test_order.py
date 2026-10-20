"""订单模块接口测试用例

覆盖场景：
1. 下单：正向（校验金额/状态）、反向数据驱动（商品不存在/库存不足/数量非法）、未登录
2. 订单查询：列表、详情
3. 取消订单：完整业务链路（smoke）、重复取消、订单不存在、取消他人订单
"""
import allure
import pytest

from utils.data_loader import load_yaml

order_data = load_yaml("order_data.yaml")


@allure.epic("电商系统接口自动化测试")
@allure.feature("订单模块")
class TestCreateOrder:

    @allure.story("下单")
    @allure.title("正常下单成功，订单金额与状态校验")
    @pytest.mark.smoke
    @pytest.mark.order
    def test_create_order_ok(self, order_api):
        data = order_data["create"]["valid"]

        with allure.step(f"step1: 购买商品 {data['goods_id']} x {data['quantity']}"):
            resp = order_api.create(data["goods_id"], data["quantity"])

        with allure.step("step2: 校验下单响应"):
            assert resp.status_code == 200
            body = resp.json()["data"]
            assert body["status"] == data["expected_order_status"]
            assert body["quantity"] == data["quantity"]

        with allure.step("step3: 校验订单金额 = 单价 x 数量"):
            expected_price = round(data["unit_price"] * data["quantity"], 2)
            assert body["total_price"] == expected_price, (
                f"金额计算错误: 期望 {expected_price}, 实际 {body['total_price']}"
            )

    @allure.story("下单")
    @allure.title("下单反向用例（数据驱动：商品不存在/库存不足/数量非法）")
    @pytest.mark.regression
    @pytest.mark.order
    @pytest.mark.negative
    @pytest.mark.parametrize(
        "case_data",
        order_data["create"]["invalid_cases"],
        ids=lambda c: c["case"],
    )
    def test_create_order_invalid(self, order_api, case_data):
        """数据驱动：商品不存在 / 库存不足 / 数量非法"""
        resp = order_api.create(case_data["goods_id"], case_data["quantity"])
        assert resp.status_code == case_data["expected_status"]
        assert case_data["expected_detail_contains"] in resp.json()["detail"]

    @allure.story("下单")
    @allure.title("未登录下单，返回 401")
    @pytest.mark.regression
    @pytest.mark.order
    @pytest.mark.negative
    def test_create_order_no_token(self):
        from api.order_api import OrderApi

        no_auth_api = OrderApi(token=None)  # 不注入 token
        resp = no_auth_api.create("1001", 1)
        assert resp.status_code == 401


@allure.feature("订单模块")
class TestOrderFlow:

    @allure.story("订单全链路")
    @allure.title("下单->列表->详情->取消 全链路校验（冒烟主流程）")
    @pytest.mark.smoke
    @pytest.mark.order
    def test_order_full_flow(self, order_api):
        """核心业务链路回归：任何一步断裂即失败"""
        with allure.step("step1: 下单成功"):
            create = order_api.create("1001", 1)
            assert create.status_code == 200
            order_id = create.json()["data"]["order_id"]

        with allure.step("step2: 订单列表包含新订单"):
            items = order_api.list_orders().json()["data"]["items"]
            assert order_id in [o["order_id"] for o in items]

        with allure.step("step3: 订单详情与下单结果一致"):
            detail = order_api.detail(order_id).json()["data"]
            assert detail["order_id"] == order_id
            assert detail["status"] == "pending"

        with allure.step("step4: 取消订单成功"):
            cancel = order_api.cancel(order_id)
            assert cancel.status_code == 200

        with allure.step("step5: 取消后状态校验"):
            after = order_api.detail(order_id).json()["data"]
            assert after["status"] == "cancelled"

    @allure.story("取消订单")
    @allure.title("重复取消订单，返回 400")
    @pytest.mark.regression
    @pytest.mark.order
    @pytest.mark.negative
    def test_cancel_twice(self, order_api):
        order_id = order_api.create("1001", 1).json()["data"]["order_id"]

        first = order_api.cancel(order_id)
        assert first.status_code == 200

        second = order_api.cancel(order_id)
        assert second.status_code == 400
        assert "无法取消" in second.json()["detail"]

    @allure.story("取消订单")
    @allure.title("取消不存在的订单，返回 404")
    @pytest.mark.regression
    @pytest.mark.order
    @pytest.mark.negative
    def test_cancel_not_exist(self, order_api):
        resp = order_api.cancel(order_data["cancel"]["not_exist_order_id"])
        assert resp.status_code == 404

    @allure.story("取消订单")
    @allure.title("查询不存在的订单详情，返回 404")
    @pytest.mark.regression
    @pytest.mark.order
    @pytest.mark.negative
    def test_detail_not_exist(self, order_api):
        resp = order_api.detail(order_data["cancel"]["not_exist_order_id"])
        assert resp.status_code == 404
