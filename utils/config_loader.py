"""配置管理：加载 config/config.yaml，支持多环境切换

优先级：环境变量 ENV > 文件中的 default_env
用法：$env:ENV="test"; pytest   （即可切换到 test 环境跑用例）
"""
import os

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "config.yaml")


def load_config(env: str | None = None) -> dict:
    """读取指定环境的配置，返回 {base_url, timeout, username, password, ...}"""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    env = env or os.getenv("ENV") or config["default_env"]
    if env not in config["env"]:
        raise ValueError(f"未知环境: {env}，可选: {list(config['env'].keys())}")
    return config["env"][env]


def project_root() -> str:
    """返回项目根目录（定位测试数据等资源时使用）"""
    return _PROJECT_ROOT
