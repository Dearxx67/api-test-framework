"""测试数据加载：统一从 testdata/ 目录取 YAML，实现用例数据与脚本分离"""
import os

import yaml

from utils.config_loader import project_root


def load_yaml(filename: str) -> dict:
    """加载 testdata/ 下的 YAML 文件并返回 dict"""
    path = os.path.join(project_root(), "testdata", filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
