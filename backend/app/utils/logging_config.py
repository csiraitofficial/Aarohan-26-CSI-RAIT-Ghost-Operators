import logging
import json
import time
from datetime import datetime
from typing import Any

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON for production log management (ELK/Splunk).
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra context if available (via 'extra' kwarg in logging)
        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
            
        return json.dumps(log_record)

def setup_production_logging():
    """
    Configures the root logger for production-grade JSON output.
    """
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Also log to a file for persistent audit
    file_handler = logging.FileHandler("logs/security_audit.json")
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    logging.info("Production JSON Logging Initialized")
