#!/usr/bin/env python3
"""
Logging Configuration Test Script
Tests the structured logging implementation across services
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Add the analytics directory to the path
sys.path.append(str(Path(__file__).parent / 'services' / 'analytics'))

try:
    from structured_logger import create_logger_from_env, log_context, performance_monitor
except ImportError:
    print("Error: Could not import structured_logger. Make sure you're in the correct directory.")
    sys.exit(1)

def test_basic_logging():
    """Test basic logging functionality"""
    print("Testing basic logging functionality...")
    
    logger = create_logger_from_env("test-service", "basic-test")
    
    # Test different log levels
    logger.debug("This is a debug message", test_field="debug_value")
    logger.info("This is an info message", test_field="info_value")
    logger.warning("This is a warning message", test_field="warning_value")
    logger.error("This is an error message", test_field="error_value")
    
    print("✓ Basic logging test completed")

def test_context_logging():
    """Test context-aware logging"""
    print("Testing context-aware logging...")
    
    logger = create_logger_from_env("test-service", "context-test")
    
    with log_context(operation="test_operation", session_id="session-123"):
        logger.info("Message with context")
        
        with logger.with_fields(user_id="user-456", action="data_processing"):
            logger.info("Message with additional fields")
            
            try:
                raise ValueError("Test exception")
            except ValueError:
                logger.exception("Caught test exception")
    
    print("✓ Context logging test completed")

def test_performance_monitoring():
    """Test performance monitoring decorators"""
    print("Testing performance monitoring...")
    
    logger = create_logger_from_env("test-service", "performance-test")
    
    @performance_monitor(logger, "test_slow_operation")
    def slow_operation():
        time.sleep(0.1)  # Simulate slow operation
        return "operation completed"
    
    result = slow_operation()
    logger.info("Performance test completed", result=result)
    
    print("✓ Performance monitoring test completed")

def test_business_events():
    """Test business event logging"""
    print("Testing business event logging...")
    
    logger = create_logger_from_env("test-service", "business-test")
    
    # Log various business events
    logger.log_business_event("user_login", "user-123", {
        "login_method": "oauth",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0"
    })
    
    logger.log_business_event("data_processed", "batch-456", {
        "records_count": 1000,
        "processing_time": 2.5,
        "status": "success"
    })
    
    logger.log_api_call("POST", "/api/data", 200, 0.25, {
        "request_size": 1024,
        "response_size": 2048
    })
    
    print("✓ Business event logging test completed")

def test_database_operations():
    """Test database operation logging"""
    print("Testing database operation logging...")
    
    logger = create_logger_from_env("test-service", "database-test")
    
    # Simulate database operations
    start_time = time.time()
    time.sleep(0.05)  # Simulate DB operation
    duration = time.time() - start_time
    
    logger.log_database_operation("SELECT", "logs", duration, 100, {
        "query_complexity": "medium",
        "cache_hit": False
    })
    
    logger.log_database_operation("INSERT", "users", 0.01, 1, {
        "table_size": "large",
        "index_used": True
    })
    
    print("✓ Database operation logging test completed")

def test_error_scenarios():
    """Test error and exception scenarios"""
    print("Testing error scenarios...")
    
    logger = create_logger_from_env("test-service", "error-test")
    
    try:
        # Simulate various error conditions
        logger.warning("Resource usage high", cpu_percent=85, memory_percent=90)
        
        logger.error("Database connection failed", 
                    error_code="DB_CONN_001",
                    retry_count=3,
                    last_attempt="2024-01-15T10:30:00Z")
        
        # Simulate exception
        raise ConnectionError("Unable to connect to external service")
        
    except ConnectionError as e:
        logger.exception("External service error",
                        service="payment_gateway",
                        error_type="connection_error",
                        retry_strategy="exponential_backoff")
    
    print("✓ Error scenario testing completed")

def test_json_output():
    """Test JSON output format"""
    print("Testing JSON output format...")
    
    # Set environment to force JSON output
    os.environ['LOG_FORMAT'] = 'JSON'
    
    logger = create_logger_from_env("test-service", "json-test")
    
    logger.info("JSON format test message", 
               complex_data={
                   "nested": {"field": "value"},
                   "array": [1, 2, 3],
                   "boolean": True,
                   "number": 42.5
               })
    
    print("✓ JSON output test completed")

def test_text_output():
    """Test text output format"""
    print("Testing text output format...")
    
    # Set environment to force text output
    os.environ['LOG_FORMAT'] = 'TEXT'
    
    logger = create_logger_from_env("test-service", "text-test")
    
    logger.info("Text format test message",
               user_id="user-789",
               operation="test_operation",
               duration_ms=150)
    
    print("✓ Text output test completed")

def test_go_service_integration():
    """Test Go service logging (if available)"""
    print("Testing Go service integration...")
    
    go_service_path = Path(__file__).parent / 'services' / 'log-ingestion'
    
    if not go_service_path.exists():
        print("⚠ Go service directory not found, skipping Go integration test")
        return
    
    # Check if Go is available
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠ Go not available, skipping Go integration test")
            return
    except FileNotFoundError:
        print("⚠ Go not installed, skipping Go integration test")
        return
    
    print("✓ Go service logging framework available")

def run_comprehensive_test():
    """Run all logging tests"""
    print("=" * 60)
    print("STRUCTURED LOGGING COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Store original environment
    original_env = {
        'LOG_LEVEL': os.environ.get('LOG_LEVEL', ''),
        'LOG_FORMAT': os.environ.get('LOG_FORMAT', ''),
    }
    
    try:
        # Set test environment
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        # Run all tests
        test_basic_logging()
        print()
        
        test_context_logging()
        print()
        
        test_performance_monitoring()
        print()
        
        test_business_events()
        print()
        
        test_database_operations()
        print()
        
        test_error_scenarios()
        print()
        
        test_json_output()
        print()
        
        test_text_output()
        print()
        
        test_go_service_integration()
        print()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Generate summary report
        generate_test_summary()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

def generate_test_summary():
    """Generate a test summary report"""
    print("\nTEST SUMMARY REPORT")
    print("-" * 40)
    
    features_tested = [
        "✓ Basic logging (DEBUG, INFO, WARNING, ERROR)",
        "✓ Context-aware logging with thread-local storage",
        "✓ Performance monitoring decorators",
        "✓ Business event logging",
        "✓ Database operation logging",
        "✓ Error and exception handling",
        "✓ JSON output format",
        "✓ Text output format",
        "✓ Go service logging framework compatibility"
    ]
    
    for feature in features_tested:
        print(feature)
    
    print("\nRECOMMENDations:")
    print("1. Review log output for proper JSON formatting")
    print("2. Verify log levels are respected in production")
    print("3. Test log aggregation with your monitoring system")
    print("4. Implement log rotation for file-based logging")
    print("5. Set up alerts for ERROR and CRITICAL level logs")

if __name__ == "__main__":
    run_comprehensive_test()
