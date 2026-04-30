"""
Structured JSON Logging Utility
===============================
Provides context-aware structured logging for trading operations.
"""

import json
import logging
import sys
import traceback
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional
from contextvars import ContextVar

from .redaction import redact_secrets, sanitize_text

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
client_id_var: ContextVar[str] = ContextVar('client_id', default='')


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_text(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context variables
        if request_id_var.get():
            log_data["request_id"] = request_id_var.get()
        if client_id_var.get():
            log_data["client_id"] = client_id_var.get()
        
        # Add extra fields from record
        if hasattr(record, 'extra_data'):
            log_data.update(redact_secrets(record.extra_data))
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, default=str)


class TradingLogger:
    """
    Context-aware trading logger with structured JSON output.
    
    Usage:
        logger = TradingLogger("order_service")
        logger.info("Order placed", symbol="NIFTY", order_id="123")
        logger.error("Order failed", symbol="NIFTY", error="Insufficient margin")
    """
    
    _instances: Dict[str, 'TradingLogger'] = {}
    
    def __new__(cls, name: str = "angelone"):
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str = "angelone"):
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.logger = logging.getLogger(f"angelone.{name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler for production
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.INFO)
        self.logger.addHandler(json_handler)
        
        self._initialized = True
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with extra data"""
        extra = {'extra_data': kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        extra = {'extra_data': kwargs}
        self.logger.exception(message, extra=extra)


def set_request_context(request_id: Optional[str] = None, client_id: Optional[str] = None):
    """Set context variables for request tracking"""
    if request_id:
        request_id_var.set(request_id)
    else:
        request_id_var.set(str(uuid.uuid4())[:8])
    
    if client_id:
        client_id_var.set(client_id)


def clear_request_context():
    """Clear context variables"""
    request_id_var.set('')
    client_id_var.set('')


def log_execution_time(logger: TradingLogger):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.debug(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    execution_time_ms=round(execution_time, 2)
                )
                return result
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.error(
                    f"{func.__name__} failed",
                    function=func.__name__,
                    execution_time_ms=round(execution_time, 2),
                    error=str(e)
                )
                raise
        return wrapper
    return decorator
