import logging
from pythonjsonlogger import jsonlogger
from datetime import datetime

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        # 确保时间戳是 ISO 标准格式
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logger():
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.INFO)
    
    # 避免重复添加 Handler
    if not logger.handlers:
        logHandler = logging.StreamHandler()
        # 定义 JSON 中输出的字段
        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(correlation_id)s %(path)s %(method)s %(status_code)s %(latency_ms)s %(message)s')
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        
    return logger