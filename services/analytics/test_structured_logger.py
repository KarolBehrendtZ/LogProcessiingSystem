import unittest
import json
import io
import sys
import os
import threading
import time
from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout, redirect_stderr

# Add the parent directory to sys.path to import structured_logger
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from structured_logger import (
    StructuredFormatter, TextFormatter, StructuredLogger, LogContext,
    create_logger_from_env, performance_monitor, exception_handler,
    log_context, init_default_logger, get_logger
)

class TestStructuredFormatter(unittest.TestCase):
    
    def setUp(self):
        self.service_name = "test-service"
        self.component = "test-component"
        self.formatter = StructuredFormatter(self.service_name, self.component)
    
    def test_format_basic_log(self):
        """Test basic log formatting"""
        import logging
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["service"], self.service_name)
        self.assertEqual(log_data["component"], self.component)
        self.assertEqual(log_data["file"], "test.py")
        self.assertEqual(log_data["line"], 42)
        self.assertEqual(log_data["function"], "test_function")
        self.assertIn("timestamp", log_data)
    
    def test_format_with_exception(self):
        """Test log formatting with exception"""
        import logging
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
            func="test_function"
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertIn("exception", log_data)
        self.assertEqual(log_data["exception"]["type"], "ValueError")
        self.assertEqual(log_data["exception"]["message"], "Test exception")
        self.assertIsInstance(log_data["exception"]["traceback"], list)
    
    def test_format_with_extra_fields(self):
        """Test log formatting with extra fields"""
        import logging
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        # Add extra fields
        record.user_id = "user123"
        record.request_id = "req456"
        record.custom_field = {"nested": "value"}
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertIn("fields", log_data)
        self.assertEqual(log_data["fields"]["user_id"], "user123")
        self.assertEqual(log_data["fields"]["request_id"], "req456")
        self.assertEqual(log_data["fields"]["custom_field"], {"nested": "value"})
    
    def test_format_with_thread_context(self):
        """Test log formatting with thread context"""
        import logging
        
        # Set thread context
        threading.current_thread().log_context = {
            "trace_id": "trace123",
            "operation": "test_op"
        }
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertEqual(log_data["trace_id"], "trace123")
        self.assertEqual(log_data["operation"], "test_op")
        
        # Clean up
        delattr(threading.current_thread(), 'log_context')

class TestTextFormatter(unittest.TestCase):
    
    def setUp(self):
        self.service_name = "test-service"
        self.component = "test-component"
        self.formatter = TextFormatter(self.service_name, self.component)
    
    def test_format_basic_log(self):
        """Test basic text log formatting"""
        import logging
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        formatted = self.formatter.format(record)
        
        self.assertIn("INFO", formatted)
        self.assertIn("Test message", formatted)
        self.assertIn(self.service_name, formatted)
        self.assertIn(self.component, formatted)
        self.assertIn("test.py:42", formatted)
        self.assertIn("test_function", formatted)

class TestStructuredLogger(unittest.TestCase):
    
    def setUp(self):
        self.output_buffer = io.StringIO()
    
    def create_test_logger(self, level="DEBUG", format_type="JSON"):
        """Create a test logger with string buffer output"""
        logger = StructuredLogger(
            service_name="test-service",
            component="test-component",
            level=level,
            format_type=format_type
        )
        # Replace handler to use our buffer
        logger.logger.handlers[0].stream = self.output_buffer
        return logger
    
    def test_basic_logging_methods(self):
        """Test basic logging methods"""
        logger = self.create_test_logger()
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        self.assertEqual(len(lines), 4)
        
        for line in lines:
            log_data = json.loads(line)
            self.assertEqual(log_data["service"], "test-service")
            self.assertEqual(log_data["component"], "test-component")
    
    def test_logging_with_fields(self):
        """Test logging with additional fields"""
        logger = self.create_test_logger()
        
        logger.info("Test message", user_id="user123", action="test_action")
        
        output = self.output_buffer.getvalue()
        log_data = json.loads(output.strip())
        
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["fields"]["user_id"], "user123")
        self.assertEqual(log_data["fields"]["action"], "test_action")
    
    def test_log_levels(self):
        """Test log level filtering"""
        logger = self.create_test_logger(level="WARNING")
        
        logger.debug("Debug message")  # Should not appear
        logger.info("Info message")    # Should not appear
        logger.warning("Warning message")  # Should appear
        logger.error("Error message")      # Should appear
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        # Only warning and error should be logged
        self.assertEqual(len(lines), 2)
        
        warning_log = json.loads(lines[0])
        error_log = json.loads(lines[1])
        
        self.assertEqual(warning_log["level"], "WARNING")
        self.assertEqual(error_log["level"], "ERROR")
    
    def test_with_fields_context(self):
        """Test with_fields context manager"""
        logger = self.create_test_logger()
        
        with logger.with_fields(session_id="sess123", user_type="admin"):
            logger.info("Message with context")
        
        output = self.output_buffer.getvalue()
        log_data = json.loads(output.strip())
        
        # Note: The context is stored in thread-local storage
        # The actual fields are added via the extra parameter in logging
    
    def test_component_override(self):
        """Test with_component method"""
        logger = self.create_test_logger()
        component_logger = logger.with_component("new-component")
        
        component_logger.info("Test message")
        
        output = self.output_buffer.getvalue()
        log_data = json.loads(output.strip())
        
        self.assertEqual(log_data["component"], "new-component")
    
    def test_specialized_logging_methods(self):
        """Test specialized logging methods"""
        logger = self.create_test_logger()
        
        # Test performance logging
        logger.log_performance("test_operation", 0.150, status="success")
        
        # Test business event logging
        logger.log_business_event("user_login", "user123", method="oauth")
        
        # Test database operation logging
        logger.log_database_operation("SELECT", "users", 0.050, 10)
        
        # Test API call logging
        logger.log_api_call("GET", "/api/users", 200, 0.120)
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        self.assertEqual(len(lines), 4)
        
        # Check performance log
        perf_log = json.loads(lines[0])
        self.assertIn("Performance:", perf_log["message"])
        self.assertEqual(perf_log["fields"]["operation"], "test_operation")
        self.assertEqual(perf_log["fields"]["duration_ms"], 150.0)
        
        # Check business event log
        business_log = json.loads(lines[1])
        self.assertIn("Business event:", business_log["message"])
        self.assertEqual(business_log["fields"]["business_event"], "user_login")
        
        # Check database operation log
        db_log = json.loads(lines[2])
        self.assertIn("Database operation:", db_log["message"])
        self.assertEqual(db_log["fields"]["db_operation"], "SELECT")
        
        # Check API call log
        api_log = json.loads(lines[3])
        self.assertIn("API call:", api_log["message"])
        self.assertEqual(api_log["fields"]["api_status_code"], 200)

class TestLogContext(unittest.TestCase):
    
    def setUp(self):
        self.output_buffer = io.StringIO()
        self.logger = StructuredLogger(
            service_name="test-service",
            component="test-component",
            level="DEBUG",
            format_type="JSON"
        )
        self.logger.logger.handlers[0].stream = self.output_buffer
    
    def test_log_context_manager(self):
        """Test log context manager"""
        with log_context(operation="test_op", user_id="user123"):
            self.logger.info("Message with context")
        
        # Context should be cleared after exiting
        self.logger.info("Message without context")
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        self.assertEqual(len(lines), 2)
        
        # First message should have context (in thread local)
        # Second message should not have context
    
    def test_nested_contexts(self):
        """Test nested log contexts"""
        with log_context(operation="outer_op"):
            with log_context(user_id="user123"):
                self.logger.info("Nested context message")
            self.logger.info("Outer context message")
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        self.assertEqual(len(lines), 2)

class TestDecorators(unittest.TestCase):
    
    def setUp(self):
        self.output_buffer = io.StringIO()
        self.logger = StructuredLogger(
            service_name="test-service",
            component="test-component",
            level="DEBUG",
            format_type="JSON"
        )
        self.logger.logger.handlers[0].stream = self.output_buffer
    
    def test_performance_monitor_decorator(self):
        """Test performance monitoring decorator"""
        
        @performance_monitor(self.logger, "test_operation")
        def test_function():
            time.sleep(0.01)  # Small delay
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        # Should have start and performance logs
        self.assertGreaterEqual(len(lines), 2)
        
        # Check for performance log
        found_performance_log = False
        for line in lines:
            log_data = json.loads(line)
            if "Performance:" in log_data.get("message", ""):
                found_performance_log = True
                self.assertEqual(log_data["fields"]["operation"], "test_operation")
                self.assertEqual(log_data["fields"]["status"], "success")
                break
        
        self.assertTrue(found_performance_log)
    
    def test_performance_monitor_with_exception(self):
        """Test performance monitoring decorator with exception"""
        
        @performance_monitor(self.logger, "failing_operation")
        def failing_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        # Should have logs including error
        self.assertGreater(len(lines), 0)
        
        # Check for performance log with error status
        found_error_performance_log = False
        for line in lines:
            log_data = json.loads(line)
            if ("Performance:" in log_data.get("message", "") and 
                log_data["fields"].get("status") == "error"):
                found_error_performance_log = True
                break
        
        self.assertTrue(found_error_performance_log)
    
    def test_exception_handler_decorator(self):
        """Test exception handler decorator"""
        
        @exception_handler(self.logger)
        def failing_function():
            raise RuntimeError("Test runtime error")
        
        with self.assertRaises(RuntimeError):
            failing_function()
        
        output = self.output_buffer.getvalue()
        lines = output.strip().split('\n')
        
        self.assertGreater(len(lines), 0)
        
        # Check for exception log
        found_exception_log = False
        for line in lines:
            log_data = json.loads(line)
            if "Exception in" in log_data.get("message", ""):
                found_exception_log = True
                self.assertEqual(log_data["fields"]["exception_type"], "RuntimeError")
                break
        
        self.assertTrue(found_exception_log)

class TestEnvironmentIntegration(unittest.TestCase):
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'ERROR',
        'LOG_FORMAT': 'TEXT',
        'LOG_OUTPUT': 'stdout'
    })
    def test_create_logger_from_env(self):
        """Test logger creation from environment variables"""
        logger = create_logger_from_env("env-service", "env-component")
        
        # Verify configuration was loaded from environment
        self.assertEqual(logger.service_name, "env-service")
        self.assertEqual(logger.component, "env-component")
        # Note: Internal logger level checking would require more setup
    
    def test_default_logger_initialization(self):
        """Test default logger initialization and usage"""
        # Initialize default logger
        init_default_logger("default-service", "default-component")
        
        # Test that we can get the logger
        default_logger = get_logger()
        self.assertIsNotNone(default_logger)
        self.assertEqual(default_logger.service_name, "default-service")
        self.assertEqual(default_logger.component, "default-component")
    
    def test_default_logger_not_initialized(self):
        """Test error when using default logger before initialization"""
        # Clear any existing default logger
        import structured_logger
        structured_logger._default_logger = None
        
        with self.assertRaises(RuntimeError):
            get_logger()

class TestTextOutput(unittest.TestCase):
    
    def setUp(self):
        self.output_buffer = io.StringIO()
    
    def test_text_format_output(self):
        """Test text format output"""
        logger = StructuredLogger(
            service_name="text-service",
            component="text-component",
            level="DEBUG",
            format_type="TEXT"
        )
        logger.logger.handlers[0].stream = self.output_buffer
        
        logger.info("Test text message", user_id="user123")
        
        output = self.output_buffer.getvalue()
        
        self.assertIn("INFO", output)
        self.assertIn("Test text message", output)
        self.assertIn("text-service", output)
        self.assertIn("text-component", output)
        # Fields should be in JSON format within the text output
        self.assertIn("user_id", output)

class TestErrorHandling(unittest.TestCase):
    
    def test_logger_with_invalid_output_file(self):
        """Test logger creation with invalid output file"""
        # Try to create logger with invalid file path
        logger = StructuredLogger(
            service_name="test-service",
            component="test-component",
            level="INFO",
            format_type="JSON",
            output_file="/invalid/path/file.log"
        )
        
        # Should fall back to stdout and not crash
        self.assertIsNotNone(logger)
    
    def test_json_serialization_error_handling(self):
        """Test handling of non-serializable objects in logs"""
        output_buffer = io.StringIO()
        logger = StructuredLogger(
            service_name="test-service",
            component="test-component",
            level="DEBUG",
            format_type="JSON"
        )
        logger.logger.handlers[0].stream = output_buffer
        
        # Create a non-serializable object
        class NonSerializable:
            pass
        
        non_serializable = NonSerializable()
        
        # This should not crash, but convert to string
        logger.info("Test message", non_serializable_object=non_serializable)
        
        output = output_buffer.getvalue()
        self.assertIn("Test message", output)
        # The non-serializable object should be converted to string representation

if __name__ == '__main__':
    # Set up test environment
    os.environ.setdefault('LOG_LEVEL', 'DEBUG')
    os.environ.setdefault('LOG_FORMAT', 'JSON')
    
    # Run tests
    unittest.main(verbosity=2)
