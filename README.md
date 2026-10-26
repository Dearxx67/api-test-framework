# 基于 Pytest 的接口自动化测试框架

轻量级接口自动化测试框架：**Python + Requests + Pytest + Allure + Jenkins + Locust + Faker**，对模拟电商后端的用户/订单接口开展回归自动化测试。

## 框架特性

- **三层架构**：用例层(testcases) → 接口层(api) → 工具层(utils)，用例与请求细节解耦
- **数据驱动**：用例数据与脚本分离（testdata/*.yaml），新增用例只加数据不改代码
- **用例标签**：smoke / regression / negative / user / order / mock，支持任意组合筛选执行
- **前置隔离**：fixture 分层（session 级 API 实例复用 + function 级随机账号），用例零依赖、可重复执行
- **依赖隔离**：responses 库 Mock 第三方依赖，成功/超时/500 等异常场景稳定复现
- **测试报告**：Allure 可视化报告（epic/feature/story 分层 + step 步骤 + 失败日志）
- **持续集成**：Jenkins 声明式流水线（Jenkinsfile），提交代码自动执行用例并生成报告；附 GitHub Actions 双轨方案
- **性能压测**：Locust 混合场景压测（模拟真实用户行为模型），输出吞吐量、P50/P95/P99 响应时间

## 目录结构

```
api-test-framework/
├── api/                  # 接口封装层
│   ├── base_api.py       # requests 二次封装：Session 复用/统一日志/统一超时
│   ├── user_api.py       # 用户模块：注册/登录/信息查询
│   └── order_api.py      # 订单模块：创建/列表/详情/取消
├── testcases/            # 测试用例层（Pytest）
│   ├── conftest.py       # 全局 fixture：API 实例/随机账号/登录态注入
│   ├── test_user.py      # 用户模块用例（正向+反向+鉴权）
│   ├── test_order.py     # 订单模块用例（数据驱动+全链路）
│   └── test_mock_demo.py # Mock 依赖隔离演示（responses）
├── testdata/             # 测试数据（YAML，数据与脚本分离）
├── utils/                # 工具层
│   ├── config_loader.py  # 多环境配置（ENV 环境变量切换 dev/test/prod）
│   ├── data_loader.py    # YAML 数据加载
│   ├── data_factory.py   # Faker 数据工厂（随机造数/批量造数）
│   └── log_util.py       # 日志（控制台+文件双输出）
├── mock_server/app.py    # FastAPI 模拟电商后端（被测服务，项目可独立运行）
├── locustfiles/locustfile.py  # Locust 压测脚本（混合场景行为建模）
├── config/config.yaml    # 环境配置
├── Jenkinsfile           # Jenkins 声明式流水线
├── .github/workflows/ci.yml   # GitHub Actions 备选 CI
├── pytest.ini            # Pytest 配置 + marker 定义
└── requirements.txt
```

## 快速开始

```bash
# 1. 安装依赖
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# source .venv/bin/pip install -r requirements.txt  # Linux/Mac

# 2. 启动被测服务（模拟电商后端）
.venv/Scripts/python -m uvicorn mock_server.app:app --port 8000

# 3. 执行全部用例
.venv/Scripts/python -m pytest

# 按标签筛选执行
.venv/Scripts/python -m pytest -m smoke          # 只跑冒烟
.venv/Scripts/python -m pytest -m "order and negative"  # 组合筛选

# 4. 生成/查看 Allure 报告（需 allure 命令行）
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report

# 5. 压测（20 并发用户，每秒起 2 个，持续 15 秒）
.venv/Scripts/python -m locust -f locustfiles/locustfile.py \
    --host http://127.0.0.1:8000 -u 20 -r 2 -t 15s --headless --csv reports/locust_stats
```

切换测试环境：`set ENV=test && pytest`（Windows）/ `ENV=test pytest`（Linux）

## 查看测试报告（三种方式，按需选用）

**方式一：单文件 HTML 报告（推荐分享给他人，零门槛）**

跑完 pytest 后自动生成 `reports/report.html`——**双击直接在浏览器打开**，无需安装任何工具。
（由 pytest-html 插件生成，`--self-contained-html` 参数把样式全部内联进单文件，方便直接分享）

**方式二：Allure 完整报告（本机已装 allure CLI + Java）**

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report --port 9090   # 浏览器访问 http://127.0.0.1:9090
```
提供 epic/feature/story 业务分层、step 步骤、失败断言详情等完整视图。

**方式三：云端报告（无需 clone 项目）**

GitHub 仓库 → Actions 页 → 任意一次运行 → Artifacts 区下载 `html-report`（单文件报告）
与 `allure-results`（原始数据），前者直接打开，后者供深入分析。

## 压测指标示例（20 并发用户 / 15s）

| 指标 | 数值 |
|------|------|
| 总请求 / 失败率 | 228 / 0.00% |
| 聚合吞吐量 | 16.71 req/s |
| 响应时间 P50 / P95 / P99 | 2ms / 5ms / 15ms |

## CI 说明

- **Jenkins**：使用 `Jenkinsfile`（声明式流水线）：拉代码 → 装依赖 → 起服务（健康检查）→ 跑用例 → Allure 插件渲染报告 → 失败自动归档日志
- **GitHub Actions**：`.github/workflows/ci.yml`，push/PR 触发，Allure 结果作为 Artifact 上传
