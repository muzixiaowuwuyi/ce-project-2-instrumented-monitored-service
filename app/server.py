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
NAMESPACE = "Observability/AppMetrics"

# 混沌工程：故障注入开关（默认全部关闭，保持健康状态）
DEGRADED = {
    "checkout": False,
    "products": False,
    "user_login": False,
    "analytics": False
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
        # 激活 ContextVars 处理器，允许跨函数共享同一请求的全局 UUID (correlation_id)
        structlog.contextvars.merge_contextvars,
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
def put_metric(metric_name, value, endpoint, extra_dimensions=None):
    """
    通用自定义指标推送器。支持添加多维度（Dimensions）标签，便于大盘进行多维度筛选过滤。
    """
    dimensions = [{'Name': 'Endpoint', 'Value': endpoint}]
    if extra_dimensions:
        for k, v in extra_dimensions.items():
            dimensions.append({'Name': k, 'Value': str(v)})

    # 判断单位
    if 'Count' in metric_name or 'Rate' in metric_name:
        unit = 'Count'
    elif 'Status' in metric_name:
        unit = 'None'
    else:
        unit = 'Milliseconds'

    try:
        cw.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': dimensions,
                    'Value': value,
                    'Unit': unit
                }
            ]
        )
    except Exception as metric_err:
        logger.warning("failed_to_push_metric", error=str(metric_err))

# -----------------------------
# 6. 核心：高级可观测性魔法装饰器
# -----------------------------
def observe(endpoint_name):
    def wrapper(func):
        def inner(*args, **kwargs):
            start = time.time()
            correlation_id = str(uuid.uuid4())
            
            # 【核心优化】：将 correlation_id 动态绑定到当前线程上下文中
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id, endpoint=endpoint_name)

            status_code = 200
            try:
                # 执行真实业务
                response = func(*args, **kwargs)
                
                # 兼容 Flask 返回 tuple（如 (body, status)）或普通 response 的场景
                if isinstance(response, tuple) and len(response) > 1:
                    status_code = response[1]
                
                duration = (time.time() - start) * 1000

                # 打印全局统一格式的成功日志
                logger.info(
                    "request_completed",
                    duration_ms=duration,
                    http_status=status_code,
                    status="success"
                )

                # 推送大盘黄金核心指标
                put_metric("RequestCount", 1, endpoint_name, {"HttpStatus": status_code})
                put_metric("LatencyMs", duration, endpoint_name)

                return response

            except Exception as e:
                duration = (time.time() - start) * 1000
                status_code = 500

                # 打印全局统一格式的失败日志
                logger.error(
                    "request_failed",
                    duration_ms=duration,
                    http_status=status_code,
                    error=str(e),
                    status="error"
                )

                # 推送错误和状态码指标，用于大盘报警与饼图分类
                put_metric("RequestCount", 1, endpoint_name, {"HttpStatus": status_code})
                put_metric("ErrorCount", 1, endpoint_name)
                put_metric("LatencyMs", duration, endpoint_name)
                raise
            finally:
                # 请求结束，清理上下文，防止内存泄漏
                structlog.contextvars.clear_contextvars()

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
        "application": "CloudWatch Dashboard Mastery API",
        "status": "healthy",
        "metrics_namespace": NAMESPACE,
        "log_file": LOG_FILE_PATH,
        "degradation_status": DEGRADED,
        "available_endpoints": {
            "health": "/health",
            "products": "/products",
            "checkout": "/checkout",
            "user/login": "/user/login",
            "analytics/report": "/analytics/report",
            "toggle_degradation": "/toggle-degradation"
        }
    })

@app.route('/products')
@observe("/products")
def products():
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
@observe("/checkout")
def checkout():
    if DEGRADED["checkout"]:
        time.sleep(random.uniform(2.0, 5.0))
        if random.random() < 0.3:
            raise Exception("payment_gateway_connection_timeout")
    else:
        time.sleep(random.uniform(0.1, 0.4))

    # 【体验完美同步】：由于开启了 ContextVars，这里的业务日志会自动带上和上面 request_completed 完全相同的 correlation_id 
    logger.info(
        "order_created",
        order_id=f"ord-{uuid.uuid4().hex[:8]}",
        amount=random.uniform(10.0, 500.0), # 变成随机金额，便于在大盘上做销售额统计分析
        user_id=f"user-{random.randint(100, 999)}"
    )

    return jsonify({"message": "checkout complete", "status": "processed"})

# --- 新增路由 1: 用户认证中心（用来在大盘上模拟 401/403 权限异常指标） ---
@app.route('/user/login', methods=['POST'])
@observe("/user/login")
def user_login():
    if DEGRADED["user_login"]:
        # 故障模式下，模拟高概率的用户密码错误，返回 401
        time.sleep(random.uniform(0.1, 0.5))
        logger.warning("login_failed_bad_credentials", input_username="attacker_demo")
        return jsonify({"message": "Unauthorized: invalid credentials"}), 401
    
    time.sleep(random.uniform(0.02, 0.1))
    logger.info("login_success", user_id=f"user-{random.randint(100, 999)}")
    return jsonify({"message": "login success", "token": "jwt-token-xyz"})

# --- 新增路由 2: 大数据分析中心（用来在大盘上模拟大规模数据提取导致的高内存和高吞吐） ---
@app.route('/analytics/report')
@observe("/analytics/report")
def analytics_report():
    if DEGRADED["analytics"]:
        # 故障模式下，模拟大数据查询产生巨额耗时（例如 6-10 秒）
        time.sleep(random.uniform(6.0, 10.0))
    else:
        time.sleep(random.uniform(0.5, 1.5))
        
    processed_rows = random.randint(5000, 50000)
    logger.info("analytics_report_generated", rows_extracted=processed_rows)
    
    # 额外推送一个特定于业务的大数据量专属 Metric：ProcessedRowsCount
    put_metric("ProcessedRowsCount", processed_rows, "/analytics/report")
    
    return jsonify({"report_type": "DataOps Summary", "rows": processed_rows, "status": "generated"})

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
    logger.warning("degradation_toggled", endpoint=endpoint, enabled=enabled)

    return jsonify({"endpoint": endpoint, "degraded_mode_active": enabled})

if __name__ == '__main__':
    logger.info("application_started", port=5000, environment="production")
    app.run(host='0.0.0.0', port=5000)