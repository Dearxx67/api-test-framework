"""日志工具：统一格式、避免重复 handler、控制台 + 文件双输出"""
import logging
import os
import sys

from utils.config_loader import project_root

_LOG_DIR = os.path.join(project_root(), "reports", "logs")


def get_logger(name: str = "api_test", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # 已初始化过，直接复用
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # 文件输出（CI 上留存排查证据）
    os.makedirs(_LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(_LOG_DIR, "api_test.log"), encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.propagate = False  # 防止日志重复打印
    return logger
