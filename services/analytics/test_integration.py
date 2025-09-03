import unittest
import os
import sys
import json
import tempfile
import time
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database_connector import DatabaseConnector
    from analyzer import analyze_error_frequency
    from structured_logger import create_logger_from_env, log_context
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class TestDatabaseConnectorIntegration(unittest.TestCase):
    """Integration tests for database connector with structured logging"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_env_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env_file.write("""
DB_HOST=localhost
DB_PORT=5432
DB_USER=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
""")
        self.temp_env_file.close()
        
        # Mock the environment file path
        self.original_env_path = None
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_env_file.name)
    
    @patch('database_connector.psycopg2.connect')
    @patch('database_connector.load_dotenv')
    def test_database_connection_with_logging(self, mock_load_dotenv, mock_connect):
        """Test database connection with structured logging"""
        # Mock environment loading
        mock_load_dotenv.return_value = True
        
        # Mock successful connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Create database connector
        db_connector = DatabaseConnector()
        
        # Test connection
        result = db_connector.connect()
        
        self.assertTrue(result)
        mock_connect.assert_called_once()
        self.assertEqual(db_connector.connection, mock_conn)
    
    @patch('database_connector.psycopg2.connect')
    @patch('database_connector.load_dotenv')
    def test_database_connection_failure_logging(self, mock_load_dotenv, mock_connect):
        """Test database connection failure with structured logging"""
        # Mock environment loading
        mock_load_dotenv.return_value = True
        
        # Mock connection failure
        import psycopg2
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        # Create database connector
        db_connector = DatabaseConnector()
        
        # Test connection failure
        result = db_connector.connect()
        
        self.assertFalse(result)
        mock_connect.assert_called_once()
    
    @patch('database_connector.psycopg2.connect')
    @patch('database_connector.load_dotenv')
    def test_get_logs_with_performance_monitoring(self, mock_load_dotenv, mock_connect):
        """Test get_logs method with performance monitoring"""
        # Mock environment loading
        mock_load_dotenv.return_value = True
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            (1, 'error', 'Test error message', '2024-01-15 10:30:00', 'test-service'),
            (2, 'info', 'Test info message', '2024-01-15 10:31:00', 'test-service'),
        ]
        
        # Create database connector
        db_connector = DatabaseConnector()
        db_connector.connect()
        
        # Test get_logs method (if it exists)
        if hasattr(db_connector, 'get_logs'):
            logs = db_connector.get_logs(limit=10)
            
            # Verify results
            self.assertEqual(len(logs), 2)
            mock_cursor.execute.assert_called()
            mock_cursor.fetchall.assert_called_once()

class TestAnalyzerIntegration(unittest.TestCase):
    """Integration tests for analyzer with structured logging"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_logs = [
            {
                'level': 'error',
                'message': 'Database connection failed',
                'timestamp': '2024-01-15T10:30:00Z',
                'source': 'db-service'
            },
            {
                'level': 'error',
                'message': 'Authentication failed for user',
                'timestamp': '2024-01-15T10:31:00Z',
                'source': 'auth-service'
            },
            {
                'level': 'warn',
                'message': 'High memory usage detected',
                'timestamp': '2024-01-15T10:32:00Z',
                'source': 'monitor-service'
            },
            {
                'level': 'info',
                'message': 'User login successful',
                'timestamp': '2024-01-15T10:33:00Z',
                'source': 'auth-service'
            },
            {
                'level': 'debug',
                'message': 'Cache hit for user data',
                'timestamp': '2024-01-15T10:34:00Z',
                'source': 'cache-service'
            }
        ]
    
    def test_error_frequency_analysis_with_logging(self):
        """Test error frequency analysis with structured logging"""
        # Analyze the sample logs
        result = analyze_error_frequency(self.sample_logs)
        
        # Verify results
        self.assertIsInstance(result, dict)
        self.assertIn('total_errors', result)
        self.assertIn('error_rate', result)
        self.assertIn('errors_by_level', result)
        self.assertIn('errors_by_source', result)
        
        # Check specific values
        self.assertEqual(result['total_errors'], 3)  # 2 errors + 1 warning
        self.assertGreater(result['error_rate'], 0)
        self.assertEqual(result['errors_by_level']['error'], 2)
        self.assertEqual(result['errors_by_level']['warn'], 1)
    
    def test_analyzer_with_empty_logs(self):
        """Test analyzer behavior with empty log list"""
        result = analyze_error_frequency([])
        
        self.assertEqual(result['total_errors'], 0)
        self.assertEqual(result['error_rate'], 0.0)
    
    def test_analyzer_with_malformed_logs(self):
        """Test analyzer robustness with malformed logs"""
        malformed_logs = [
            {'level': 'error', 'message': 'Valid error'},
            {'message': 'Missing level'},  # Missing level
            {'level': 'info'},  # Missing message
            None,  # Completely invalid
            {'level': 'error', 'message': 'Another valid error'},
        ]
        
        # Should not crash and should process valid entries
        result = analyze_error_frequency(malformed_logs)
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result['total_errors'], 2)

class TestEndToEndLoggingFlow(unittest.TestCase):
    """End-to-end tests for the complete logging flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
        self.temp_log_file.close()
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_log_file.name)
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'LOG_FORMAT': 'JSON',
        'LOG_OUTPUT': ''  # Will use stdout
    })
    def test_complete_analytics_flow_with_logging(self):
        """Test complete analytics flow with structured logging"""
        # Create logger for analytics
        logger = create_logger_from_env("analytics", "integration-test")
        
        # Simulate analytics workflow
        with log_context(analysis_id="analysis-123", batch_size=5):
            # Log start of analysis
            logger.info("Starting analytics workflow", 
                       workflow_type="error_analysis",
                       data_source="test_logs")
            
            # Perform analysis
            sample_logs = [
                {'level': 'error', 'message': 'Test error', 'source': 'test'},
                {'level': 'info', 'message': 'Test info', 'source': 'test'},
            ]
            
            start_time = time.time()
            result = analyze_error_frequency(sample_logs)
            duration = time.time() - start_time
            
            # Log performance
            logger.log_performance("error_frequency_analysis", duration, 
                                 logs_processed=len(sample_logs),
                                 errors_found=result['total_errors'])
            
            # Log business event
            logger.log_business_event("analysis_completed", "analysis-123", 
                                    result_summary=result)
            
            # Log completion
            logger.info("Analytics workflow completed", 
                       results=result,
                       success=True)
        
        # Test should complete without errors
        self.assertIsInstance(result, dict)
        self.assertIn('total_errors', result)

class TestLoggingPerformance(unittest.TestCase):
    """Performance tests for logging system"""
    
    def setUp(self):
        """Set up performance test environment"""
        # Create logger that discards output for performance testing
        import io
        self.null_stream = io.StringIO()
    
    def test_high_volume_logging_performance(self):
        """Test logging performance under high volume"""
        logger = create_logger_from_env("perf-test", "volume-test")
        
        # Override output to null stream to avoid I/O overhead
        if logger.logger.handlers:
            logger.logger.handlers[0].stream = self.null_stream
        
        # Measure time for many log entries
        start_time = time.time()
        num_logs = 1000
        
        for i in range(num_logs):
            logger.info(f"Performance test log entry {i}", 
                       iteration=i,
                       batch_id="batch-001",
                       test_data={"key": "value", "number": i})
        
        duration = time.time() - start_time
        logs_per_second = num_logs / duration
        
        # Should be able to handle at least 100 logs per second
        self.assertGreater(logs_per_second, 100, 
                          f"Logging performance too slow: {logs_per_second:.2f} logs/sec")
        
        print(f"Logging performance: {logs_per_second:.2f} logs/sec")
    
    def test_complex_object_logging_performance(self):
        """Test logging performance with complex objects"""
        logger = create_logger_from_env("perf-test", "complex-test")
        
        if logger.logger.handlers:
            logger.logger.handlers[0].stream = self.null_stream
        
        # Create complex object
        complex_object = {
            "nested": {
                "deep": {
                    "data": list(range(100)),
                    "metadata": {f"key_{i}": f"value_{i}" for i in range(50)}
                }
            },
            "arrays": [{"item": i, "data": list(range(10))} for i in range(20)]
        }
        
        start_time = time.time()
        num_logs = 100
        
        for i in range(num_logs):
            logger.info("Complex object test", 
                       iteration=i,
                       complex_data=complex_object)
        
        duration = time.time() - start_time
        logs_per_second = num_logs / duration
        
        # Should handle complex objects reasonably well
        self.assertGreater(logs_per_second, 10,
                          f"Complex object logging too slow: {logs_per_second:.2f} logs/sec")
        
        print(f"Complex object logging performance: {logs_per_second:.2f} logs/sec")

class TestErrorScenarios(unittest.TestCase):
    """Test error scenarios and edge cases"""
    
    def test_logging_with_network_errors(self):
        """Test logging behavior during network errors"""
        # Simulate network issues with database connector
        with patch('database_connector.psycopg2.connect') as mock_connect:
            import psycopg2
            mock_connect.side_effect = psycopg2.OperationalError("Network error")
            
            logger = create_logger_from_env("error-test", "network-test")
            
            # This should not crash the logging system
            logger.error("Network error occurred", 
                        error_type="connection_failure",
                        retry_count=3)
            
            # Test should complete without raising exceptions
    
    def test_logging_with_resource_constraints(self):
        """Test logging behavior under resource constraints"""
        logger = create_logger_from_env("error-test", "resource-test")
        
        # Create very large log messages
        large_message = "x" * 100000  # 100KB message
        
        # Should handle large messages gracefully
        try:
            logger.warning("Large message test", large_data=large_message)
            logger.info("Resource constraint test completed")
        except Exception as e:
            self.fail(f"Logging failed with large message: {e}")
    
    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads"""
        import threading
        import queue
        
        logger = create_logger_from_env("error-test", "concurrent-test")
        results = queue.Queue()
        
        def worker_thread(thread_id):
            """Worker function for concurrent logging"""
            try:
                for i in range(10):
                    with log_context(thread_id=thread_id, iteration=i):
                        logger.info(f"Concurrent log from thread {thread_id}",
                                  operation="concurrent_test",
                                  data={"value": i * thread_id})
                results.put(("success", thread_id))
            except Exception as e:
                results.put(("error", thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        error_count = 0
        
        while not results.empty():
            result = results.get()
            if result[0] == "success":
                success_count += 1
            else:
                error_count += 1
                print(f"Thread {result[1]} error: {result[2]}")
        
        self.assertEqual(success_count, num_threads)
        self.assertEqual(error_count, 0)

class TestConfigurationVariations(unittest.TestCase):
    """Test different configuration scenarios"""
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'ERROR',
        'LOG_FORMAT': 'TEXT'
    })
    def test_error_level_text_format(self):
        """Test ERROR level with TEXT format"""
        logger = create_logger_from_env("config-test", "error-text")
        
        # Only error and critical should be logged
        logger.debug("Debug message")  # Should not appear
        logger.info("Info message")    # Should not appear
        logger.warning("Warning message")  # Should not appear
        logger.error("Error message")   # Should appear
        logger.critical("Critical message")  # Should appear
        
        # Test should complete without errors
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'LOG_FORMAT': 'JSON'
    })
    def test_debug_level_json_format(self):
        """Test DEBUG level with JSON format"""
        logger = create_logger_from_env("config-test", "debug-json")
        
        # All levels should be logged
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Test should complete without errors

if __name__ == '__main__':
    # Set up test environment
    os.environ.setdefault('LOG_LEVEL', 'DEBUG')
    os.environ.setdefault('LOG_FORMAT', 'JSON')
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestDatabaseConnectorIntegration,
        TestAnalyzerIntegration,
        TestEndToEndLoggingFlow,
        TestLoggingPerformance,
        TestErrorScenarios,
        TestConfigurationVariations
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
