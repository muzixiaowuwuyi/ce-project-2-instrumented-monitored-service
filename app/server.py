import os
import logging
import structlog
import boto3
import random
import time
import uuid
from flask import Flask, request, jsonify

# -----------------------------
# 1. 基础配置 (REGION & NAMESPACE)
# -----------------------------
# 适配你的法兰克福区域
REGION = "eu-central-1"   
# 你的自定义云端指标命名空间，可以在 CloudWatch -> Metrics -> All metrics 中直接看到这个分类
NAMESPACE = "DataOps/AppMetrics"

# 混沌工程：故障注入开关（默认全部关闭，保持健康状态）
DEGRADED = {
    "checkout": False,
    "products": False
}

# -----------------------------
# 2. 初始化 AWS CLOUDWATCH 客户端
# -----------------------------
cw = boto3.client("cloudwatch", region_name=REGION)

# -----------------------------
# 3. 结构化日志配置 (Structlog)
# -----------------------------
# 精确匹配你在 EC2 上的真实日志绝对路径
LOG_FILE_PATH = '/home/ubuntu/ce-project-2-instrumented-monitored-service/app/application.log'

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(message)s'
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# -----------------------------
# 4. FLASK 实例化
# -----------------------------
app = Flask(__name__)

# -----------------------------
# 5. AWS METRIC 推送助手函数
# -----------------------------
def put_metric(metric_name, value, endpoint):
    """
    旁路异步（向 AWS 发送自定义 Metric 指标）
    """
    try:
        cw.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': [
                        {
                            'Name': 'Endpoint',
                            'Value': endpoint
                        }
                    ],
                    'Value': value,
                    'Unit': 'Count' if 'Count' in metric_name else 'Milliseconds'
                }
            ]
        )
    except Exception as metric_err:
        # 防止 AWS 权限问题或网络抖动导致应用主业务挂掉，这里做降级捕获
        logger.warning("failed_to_push_metric", error=str(metric_err))

# -----------------------------
# 6. 核心：高级可观测性魔法装饰器
# -----------------------------
def observe(endpoint_name):
    def wrapper(func):
        def inner(*args, **kwargs):
            start = time.time()
            correlation_id = str(uuid.uuid4())

            try:
                # 执行原本的路由业务逻辑
                result = func(*args, **kwargs)

                # 计算响应延迟（毫秒）
                duration = (time.time() - start) * 1000

                # 自动打印结构化成功日志
                logger.info(
                    "request_completed",
                    endpoint=endpoint_name,
                    correlation_id=correlation_id,
                    duration_ms=duration,
                    status="success"
                )

                # 自动向 CloudWatch 推送成功计数和延迟指标
                put_metric("RequestCount", 1, endpoint_name)
                put_metric("LatencyMs", duration, endpoint_name)

                return result

            except Exception as e:
                duration = (time.time() - start) * 1000

                # 自动捕捉未处理的异常，写入最高规格的错误日志
                logger.error(
                    "request_failed",
                    endpoint=endpoint_name,
                    correlation_id=correlation_id,
                    duration_ms=duration,
                    error=str(e),
                    status="error"
                )

                # 自动向 CloudWatch 推送错误计数指标
                put_metric("ErrorCount", 1, endpoint_name)
                
                # 原封不动抛回给 Flask，确保前端能拿到正常的报错响应
                raise

        # 必须重置命名空间，防止 Flask 路由别名冲突崩溃
        inner.__name__ = func.__name__
        return inner
    return wrapper

# -----------------------------
# 7. 业务路由 (Routes)
# -----------------------------

@app.route('/health')
def health():
    return {"status": "healthy"}

@app.route('/')
def home():
    return jsonify({
        "application": "Advanced Observability Architecture API",
        "status": "healthy",
        "metrics_namespace": NAMESPACE,
        "log_file": LOG_FILE_PATH,
        "degradation_status": DEGRADED,
        "available_endpoints": {
            "health": "/health",
            "products": "/products",
            "checkout": "/checkout",
            "toggle_degradation": "/toggle-degradation"
        }
    })

@app.route('/products')
@observe("/products") # 一行装饰器，秒变高规格监控模式
def products():
    # 如果开启了故障注入，随机产生 1.5 到 4.5 秒的高延迟环境
    if DEGRADED["products"]:
        time.sleep(random.uniform(1.5, 4.5))
    else:
        time.sleep(random.uniform(0.05, 0.2))

    return jsonify({
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Keyboard", "price": 49.99}
        ]
    })

@app.route('/checkout', methods=['POST'])
@observe("/checkout") # 业务与监控逻辑完全解耦
def checkout():
    # 如果开启了故障注入，不仅慢，还有 30% 的概率直接崩溃抛出异常
    if DEGRADED["checkout"]:
        time.sleep(random.uniform(2.0, 5.0))
        if random.random() < 0.3:
            raise Exception("payment_gateway_connection_timeout")
    else:
        time.sleep(random.uniform(0.1, 0.4))

    # 业务特异性日志，依然可以和结构化日志完美融合
    logger.info(
        "order_created",
        order_id=f"ord-{uuid.uuid4().hex[:8]}",
        amount=99.99,
        user_id="user-123"
    )

    return jsonify({"message": "checkout complete", "status": "processed"})

# -----------------------------
# 8. 故障注入控制开关 (Chaos Testing)
# -----------------------------
@app.route('/toggle-degradation', methods=['POST'])
def toggle():
    data = request.get_json() or {}
    endpoint = data.get("endpoint")
    enabled = data.get("enabled")

    if endpoint not in DEGRADED:
        return jsonify({"error": f"invalid endpoint. Choose from {list(DEGRADED.keys())}"}), 400

    DEGRADED[endpoint] = bool(enabled)

    logger.warning(
        "degradation_toggled",
        endpoint=endpoint,
        enabled=enabled
    )

    return jsonify({
        "endpoint": endpoint,
        "degraded_mode_active": enabled
    })

# -----------------------------
# 9. 启动入口
# -----------------------------
if __name__ == '__main__':
    logger.info("application_started", port=5000, environment="production")
    app.run(host='0.0.0.0', port=5000)