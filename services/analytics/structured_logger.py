import logging
import json
import sys
import os
import time
import traceback
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from functools import wraps
from contextlib import contextmanager

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def __init__(self, service_name: str, component: str = ""):
        super().__init__()
        self.service_name = service_name
        self.component = component
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace('+00:00', 'Z'),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.service_name,
            "component": self.component or getattr(record, 'component', ''),
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields from extra
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'component'):
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["fields"] = extra_fields
            
        # Add context from thread local if available
        context = getattr(threading.current_thread(), 'log_context', {})
        if context:
            log_entry.update(context)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)

class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def __init__(self, service_name: str, component: str = ""):
        super().__init__()
        self.service_name = service_name
        self.component = component
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text"""
        timestamp = datetime.fromtimestamp(record.created, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        component = self.component or getattr(record, 'component', '')
        
        base_msg = f"[{timestamp}] {record.levelname} [{self.service_name}/{component}] {record.filename}:{record.lineno} {record.funcName} - {record.getMessage()}"
        
        # Add context information
        context = getattr(threading.current_thread(), 'log_context', {})
        if context:
            context_str = " ".join([f"{k}={v}" for k, v in context.items()])
            base_msg += f" [{context_str}]"
        
        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'component'):
                extra_fields[key] = value
        
        if extra_fields:
            fields_str = json.dumps(extra_fields, default=str)
            base_msg += f" fields={fields_str}"
        
        # Add exception information
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
            
        return base_msg

class StructuredLogger:
    """Structured logger with context support"""
    
    def __init__(self, service_name: str, component: str = "", level: str = "INFO", 
                 format_type: str = "JSON", output_file: Optional[str] = None):
        self.service_name = service_name
        self.component = component
        self.logger = logging.getLogger(f"{service_name}.{component}" if component else service_name)
        
        # Set level
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create handler
        if output_file:
            try:
                handler = logging.FileHandler(output_file)
            except (FileNotFoundError, PermissionError, OSError):
                # Fall back to stdout if file cannot be created
                handler = logging.StreamHandler(sys.stdout)
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        # Set formatter
        if format_type.upper() == "JSON":
            formatter = StructuredFormatter(service_name, component)
        else:
            formatter = TextFormatter(service_name, component)
            
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def with_fields(self, **fields) -> 'LogContext':
        """Create a log context with additional fields"""
        return LogContext(self, fields)
    
    def with_component(self, component: str) -> 'StructuredLogger':
        """Create a new logger with a different component"""
        # Convert numeric level back to string
        level_name = logging.getLevelName(self.logger.level)
        new_logger = StructuredLogger(
            self.service_name, 
            component, 
            level_name, 
            "JSON",  # Assume JSON for consistency
            None
        )
        
        # Inherit the output stream from the current logger
        if self.logger.handlers:
            original_handler = self.logger.handlers[0]
            new_handler = new_logger.logger.handlers[0]
            new_handler.stream = original_handler.stream
        
        return new_logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def log_performance(self, operation: str, duration: float, **fields):
        """Log performance metrics"""
        self.info(f"Performance: {operation}", 
                 operation=operation, 
                 duration_ms=duration * 1000,
                 **fields)
    
    def log_business_event(self, event: str, entity_id: str, **fields):
        """Log business-specific events"""
        self.info(f"Business event: {event}",
                 business_event=event,
                 entity_id=entity_id,
                 **fields)
    
    def log_database_operation(self, operation: str, table: str, duration: float, rows_affected: int = 0, **fields):
        """Log database operation details"""
        self.debug(f"Database operation: {operation}",
                  db_operation=operation,
                  db_table=table,
                  db_duration_ms=duration * 1000,
                  db_rows_affected=rows_affected,
                  **fields)
    
    def log_api_call(self, method: str, url: str, status_code: int, duration: float, **fields):
        """Log API call details"""
        level = 'error' if status_code >= 500 else 'warning' if status_code >= 400 else 'info'
        getattr(self, level)(f"API call: {method} {url}",
                           api_method=method,
                           api_url=url,
                           api_status_code=status_code,
                           api_duration_ms=duration * 1000,
                           **fields)

class LogContext:
    """Context manager for adding fields to log entries"""
    
    def __init__(self, logger: StructuredLogger, fields: Dict[str, Any]):
        self.logger = logger
        self.fields = fields
        self.old_context = None
    
    def __enter__(self):
        # Store current context and add new fields
        thread = threading.current_thread()
        self.old_context = getattr(thread, 'log_context', {})
        new_context = self.old_context.copy()
        new_context.update(self.fields)
        thread.log_context = new_context
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        threading.current_thread().log_context = self.old_context
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        self.logger.exception(message, **kwargs)

def create_logger_from_env(service_name: str, component: str = "") -> StructuredLogger:
    """Create a logger from environment variables"""
    level = os.getenv('LOG_LEVEL', 'INFO')
    format_type = os.getenv('LOG_FORMAT', 'JSON')
    output_file = os.getenv('LOG_OUTPUT', None)
    
    return StructuredLogger(service_name, component, level, format_type, output_file)

def performance_monitor(logger: StructuredLogger, operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                logger.debug(f"Starting operation: {operation}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(operation, duration, status="success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_performance(operation, duration, status="error", error=str(e))
                logger.exception(f"Operation failed: {operation}")
                raise
        
        return wrapper
    return decorator

def exception_handler(logger: StructuredLogger):
    """Decorator to handle and log exceptions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}",
                               function=func.__name__,
                               exception_type=type(e).__name__,
                               exception_message=str(e))
                raise
        
        return wrapper
    return decorator

@contextmanager
def log_context(**fields):
    """Context manager for adding fields to all log entries within the context"""
    thread = threading.current_thread()
    old_context = getattr(thread, 'log_context', {})
    new_context = old_context.copy()
    new_context.update(fields)
    thread.log_context = new_context
    
    try:
        yield
    finally:
        thread.log_context = old_context

# Global logger instance
_default_logger: Optional[StructuredLogger] = None

def init_default_logger(service_name: str, component: str = ""):
    """Initialize the default logger"""
    global _default_logger
    _default_logger = create_logger_from_env(service_name, component)

def get_logger() -> StructuredLogger:
    """Get the default logger"""
    if _default_logger is None:
        raise RuntimeError("Default logger not initialized. Call init_default_logger() first.")
    return _default_logger

# Convenience functions using default logger
def debug(message: str, **kwargs):
    get_logger().debug(message, **kwargs)

def info(message: str, **kwargs):
    get_logger().info(message, **kwargs)

def warning(message: str, **kwargs):
    get_logger().warning(message, **kwargs)

def error(message: str, **kwargs):
    get_logger().error(message, **kwargs)

def critical(message: str, **kwargs):
    get_logger().critical(message, **kwargs)

def exception(message: str, **kwargs):
    get_logger().exception(message, **kwargs)

# Log level configuration
def set_log_level(level: str):
    """Set log level for the default logger"""
    if _default_logger:
        _default_logger.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

def configure_logger(service_name: str, component: str = "", **config):
    """Configure a logger with custom settings"""
    return StructuredLogger(
        service_name=service_name,
        component=component,
        level=config.get('level', 'INFO'),
        format_type=config.get('format', 'JSON'),
        output_file=config.get('output_file', None)
    )
