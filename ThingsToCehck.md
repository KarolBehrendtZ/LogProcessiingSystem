Go middleware tests - Context import issue needs investigation
Go handlers tests - Need to properly implement dependency injection for database mocking
Integration tests - Still need to configure proper database environment


 SUMMARY
Total Duration: 5.92 seconds

🔵 GO TESTS
  ✅ logger: passed
    Coverage: coverage: 81.4% of statements
  ❌ middleware: failed
  ❌ handlers: failed
  ❌ benchmarks: failed

🐍 PYTHON UNIT TESTS
  ✅ structured_logger: passed

🔗 INTEGRATION TESTS
  ❌ integration: failed

🚀 PERFORMANCE TESTS
  ✅ logging_functionality: passed

💡 RECOMMENDATIONS
  • Fix failing tests: go_tests.middleware, go_tests.handlers, go_tests.benchmarks, integration_tests.integration

📄 Detailed report saved to: /mnt/c/Users/karol/Desktop/porfolio/LogProcessiingSystem/test_report.json

💥 Some tests failed. Check the report for details.