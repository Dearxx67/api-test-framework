/* Jenkins 声明式流水线：接口自动化测试 CI
 *
 * 对应 JD：「持续集成 CI/CD 接入（Jenkins），自动执行测试并生成测试报告」
 * 前置条件（Jenkins 管理员一次性配置）：
 *   1. 安装 Allure Jenkins 插件
 *   2. 全局工具中配置 Python3.12
 *
 * 触发方式：代码提交（Webhook / 轮询 SCM），失败即阻塞合入
 */
pipeline {
    agent any

    options {
        timestamps()        // 日志带时间戳，方便对照报告排查
        timeout(time: 15, unit: 'MINUTES')  // 防止用例卡死拖垮构建队列
    }

    environment {
        // 面试点：账号密码统一走 Jenkins Credentials 管理，禁止明文入库
        REPORT_PATH = 'reports/allure-results'
    }

    stages {

        stage('拉取代码') {
            steps {
                checkout scm
            }
        }

        stage('安装依赖') {
            steps {
                sh '''
                    python -m venv .venv
                    .venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
                '''
            }
        }

        stage('启动被测服务') {
            steps {
                sh '''
                    nohup .venv/bin/python -m uvicorn mock_server.app:app --port 8000 > mock_server.log 2>&1 &
                    # 健康检查重试：服务未就绪就开始跑用例会产生大片误报
                    for i in $(seq 1 10); do
                        curl -sf http://127.0.0.1:8000/health && break
                        sleep 1
                    done
                    curl -sf http://127.0.0.1:8000/health || (cat mock_server.log && exit 1)
                '''
            }
        }

        stage('执行接口自动化测试') {
            steps {
                sh '.venv/bin/pytest -m "smoke or regression" --alluredir=$REPORT_PATH'
            }
        }

        stage('生成 Allure 报告') {
            steps {
                // 依赖 Allure Jenkins 插件：历史趋势 + 失败附件直接在 Jenkins 页面查看
                allure includeProperties: false,
                       results: [[path: env.REPORT_PATH]]
            }
        }
    }

    post {
        failure {
            echo '接口自动化测试存在失败用例，请查看 Allure 报告定位！'
            archiveArtifacts artifacts: 'reports/logs/*.log, mock_server.log',
                             allowEmptyArchive: true
        }
        success {
            echo '接口自动化测试全部通过 ✅'
        }
        always {
            cleanWs()  // 清理工作区，避免脏数据影响下次构建
        }
    }
}
