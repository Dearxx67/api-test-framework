"""BaseApi：requests 二次封装，所有业务 API 类的基类

设计要点（面试考点）：
1. Session 连接复用：多次请求复用 TCP 连接，批量用例执行提速
2. 统一日志：请求前/响应后全量记录，失败可快速定位
3. 统一超时与异常：网络异常统一捕获记录后抛出，不让用例静默通过
4. 子类只关心 path 与参数，不接触底层请求细节
"""
import requests

from utils.config_loader import load_config
from utils.log_util import get_logger

logger = get_logger()


class BaseApi:
    def __init__(self, base_url: str | None = None):
        config = load_config()
        self.base_url = base_url or config["base_url"]
        self.timeout = config["timeout"]
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)

        logger.info("--> %s %s params=%s json=%s", method, url,
                    kwargs.get("params"), kwargs.get("json"))
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.RequestException as e:
            logger.error("<-- 请求异常 %s %s: %s", method, url, e)
            raise  # 必须抛出，让用例失败暴露问题，而不是静默吞掉

        # 响应体可能很长，截断防刷屏
        logger.info("<-- %s %s", resp.status_code, resp.text[:300])
        return resp

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
