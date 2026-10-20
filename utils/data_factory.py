"""测试数据工厂：基于 Faker 统一生成测试数据

为什么用数据工厂而不是写死数据？（面试考点）
1. 写死的数据重复执行会冲突（如用户名已存在导致误报）
2. 造数规则集中管理，字段变更只改一处
3. 提供批量生成能力，为压测/并发场景准备数据池
"""
from faker import Faker

fake = Faker("zh_CN")


def gen_user() -> dict:
    """生成一个可直接用于注册接口的用户数据"""
    return {
        "username": f"auto_{fake.user_name()}_{fake.random_number(digits=6)}",
        "password": fake.password(length=12, special_chars=True),
        "email": fake.email(),
    }


def gen_order(goods_id: str = "1001", quantity: int | None = None) -> dict:
    """生成一笔订单数据"""
    return {
        "goods_id": goods_id,
        "quantity": quantity if quantity is not None else fake.random_int(1, 3),
    }


def batch_users(n: int) -> list[dict]:
    """批量生成 n 个用户（为 Locust 压测准备数据池）"""
    return [gen_user() for _ in range(n)]


if __name__ == "__main__":
    # 快速自检：python utils/data_factory.py
    print("随机用户:", gen_user())
    print("随机订单:", gen_order())
    print("批量用户:", len(batch_users(100)), "个")
