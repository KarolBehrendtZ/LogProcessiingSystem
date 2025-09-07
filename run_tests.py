#!/usr/bin/env python3
"""
Comprehensive Test Runner for Log Processing System
Runs all unit tests, integration tests, and performance benchmarks
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

class TestRunner:
    """Test runner for the log processing system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'go_tests': {},
            'python_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'total_duration': 0,
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }
        self.start_time = time.time()
    
    def run_go_tests(self) -> Dict:
        """Run Go unit tests"""
        print("=" * 60)
        print("RUNNING GO UNIT TESTS")
        print("=" * 60)
        
        go_service_path = self.project_root / "services" / "log-ingestion"
        
        if not go_service_path.exists():
            print("⚠ Go service directory not found, skipping Go tests")
            return {"status": "skipped", "reason": "directory not found"}
        
        # Check if Go is available
        try:
            result = subprocess.run(['go', 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠ Go not available, skipping Go tests")
                return {"status": "skipped", "reason": "go not available"}
        except FileNotFoundError:
            print("⚠ Go not installed, skipping Go tests")
            return {"status": "skipped", "reason": "go not installed"}
        
        test_results = {}
        
        # Test logger package
        print("\n🧪 Testing logger package...")
        logger_result = self.run_go_package_tests(go_service_path / "logger")
        test_results['logger'] = logger_result
        
        # Test middleware package
        print("\n🧪 Testing middleware package...")
        middleware_result = self.run_go_package_tests(go_service_path / "middleware")
        test_results['middleware'] = middleware_result
        
        # Test handlers package
        print("\n🧪 Testing handlers package...")
        handlers_result = self.run_go_package_tests(go_service_path / "handlers")
        test_results['handlers'] = handlers_result
        
        # Run benchmarks
        print("\n📊 Running Go benchmarks...")
        benchmark_result = self.run_go_benchmarks(go_service_path)
        test_results['benchmarks'] = benchmark_result
        
        return test_results
    
    def run_go_package_tests(self, package_path: Path) -> Dict:
        """Run tests for a specific Go package"""
        if not package_path.exists():
            return {"status": "skipped", "reason": "package not found"}
        
        os.chdir(package_path)
        
        try:
            # Run tests with verbose output and coverage
            cmd = ['go', 'test', '-v', '-cover', '-coverprofile=coverage.out']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            test_output = result.stdout + result.stderr
            
            if result.returncode == 0:
                print(f"✅ {package_path.name} tests passed")
                
                # Extract coverage information
                coverage = self.extract_go_coverage(test_output)
                
                return {
                    "status": "passed",
                    "output": test_output,
                    "coverage": coverage,
                    "duration": self.extract_go_duration(test_output)
                }
            else:
                print(f"❌ {package_path.name} tests failed")
                print(test_output)
                
                return {
                    "status": "failed",
                    "output": test_output,
                    "error": "Tests failed"
                }
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {package_path.name} tests timed out")
            return {"status": "timeout", "error": "Tests timed out"}
        
        except Exception as e:
            print(f"💥 Error running {package_path.name} tests: {e}")
            return {"status": "error", "error": str(e)}
        
        finally:
            os.chdir(self.project_root)
    
    def run_go_benchmarks(self, service_path: Path) -> Dict:
        """Run Go benchmarks"""
        os.chdir(service_path)
        
        try:
            # Run benchmarks
            cmd = ['go', 'test', '-bench=.', '-benchmem', './...']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            benchmark_output = result.stdout + result.stderr
            
            if result.returncode == 0:
                print("✅ Go benchmarks completed")
                return {
                    "status": "completed",
                    "output": benchmark_output,
                    "results": self.parse_go_benchmarks(benchmark_output)
                }
            else:
                print("❌ Go benchmarks failed")
                return {
                    "status": "failed",
                    "output": benchmark_output
                }
        
        except subprocess.TimeoutExpired:
            print("⏰ Go benchmarks timed out")
            return {"status": "timeout"}
        
        except Exception as e:
            print(f"💥 Error running Go benchmarks: {e}")
            return {"status": "error", "error": str(e)}
        
        finally:
            os.chdir(self.project_root)
    
    def run_python_tests(self) -> Dict:
        """Run Python unit tests"""
        print("\n" + "=" * 60)
        print("RUNNING PYTHON UNIT TESTS")
        print("=" * 60)
        
        analytics_path = self.project_root / "services" / "analytics"
        
        if not analytics_path.exists():
            print("⚠ Analytics service directory not found, skipping Python tests")
            return {"status": "skipped", "reason": "directory not found"}
        
        test_results = {}
        
        # Test structured logger
        print("\n🧪 Testing structured logger...")
        logger_result = self.run_python_unittest(analytics_path / "test_structured_logger.py")
        test_results['structured_logger'] = logger_result
        
        return test_results
    
    def run_python_integration_tests(self) -> Dict:
        """Run Python integration tests"""
        print("\n" + "=" * 60)
        print("RUNNING PYTHON INTEGRATION TESTS")
        print("=" * 60)
        
        analytics_path = self.project_root / "services" / "analytics"
        
        if not analytics_path.exists():
            print("⚠ Analytics service directory not found, skipping integration tests")
            return {"status": "skipped", "reason": "directory not found"}
        
        test_results = {}
        
        # Run integration tests
        print("\n🧪 Testing integration scenarios...")
        integration_result = self.run_python_unittest(analytics_path / "test_integration.py")
        test_results['integration'] = integration_result
        
        return test_results
    
    def run_python_unittest(self, test_file: Path) -> Dict:
        """Run a specific Python unittest file"""
        if not test_file.exists():
            return {"status": "skipped", "reason": "test file not found"}
        
        try:
            # Change to the directory containing the test
            os.chdir(test_file.parent)
            
            # Run the unittest
            cmd = [sys.executable, test_file.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            test_output = result.stdout + result.stderr
            
            if result.returncode == 0:
                print(f"✅ {test_file.name} tests passed")
                
                return {
                    "status": "passed",
                    "output": test_output,
                    "duration": self.extract_python_duration(test_output)
                }
            else:
                print(f"❌ {test_file.name} tests failed")
                print(test_output)
                
                return {
                    "status": "failed",
                    "output": test_output,
                    "error": "Tests failed"
                }
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file.name} tests timed out")
            return {"status": "timeout", "error": "Tests timed out"}
        
        except Exception as e:
            print(f"💥 Error running {test_file.name} tests: {e}")
            return {"status": "error", "error": str(e)}
        
        finally:
            os.chdir(self.project_root)
    
    def run_logging_functionality_tests(self) -> Dict:
        """Run specific logging functionality tests"""
        print("\n" + "=" * 60)
        print("RUNNING LOGGING FUNCTIONALITY TESTS")
        print("=" * 60)
        
        test_results = {}
        
        # Run the comprehensive logging test
        print("\n🧪 Testing logging functionality...")
        logging_test_file = self.project_root / "test_logging.py"
        
        if logging_test_file.exists():
            try:
                cmd = [sys.executable, str(logging_test_file)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                test_output = result.stdout + result.stderr
                
                if result.returncode == 0:
                    print("✅ Logging functionality tests passed")
                    test_results['logging_functionality'] = {
                        "status": "passed",
                        "output": test_output
                    }
                else:
                    print("❌ Logging functionality tests failed")
                    print(test_output)
                    test_results['logging_functionality'] = {
                        "status": "failed",
                        "output": test_output
                    }
            
            except Exception as e:
                print(f"💥 Error running logging functionality tests: {e}")
                test_results['logging_functionality'] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            print("⚠ Logging functionality test file not found")
            test_results['logging_functionality'] = {
                "status": "skipped",
                "reason": "test file not found"
            }
        
        return test_results
    
    def extract_go_coverage(self, output: str) -> str:
        """Extract coverage information from Go test output"""
        lines = output.split('\n')
        for line in lines:
            if 'coverage:' in line:
                return line.strip()
        return "Coverage information not found"
    
    def extract_go_duration(self, output: str) -> str:
        """Extract test duration from Go test output"""
        lines = output.split('\n')
        for line in lines:
            if line.startswith('PASS') and 's' in line:
                return line.strip()
        return "Duration not found"
    
    def extract_python_duration(self, output: str) -> str:
        """Extract test duration from Python test output"""
        lines = output.split('\n')
        for line in lines:
            if 'Ran' in line and 'tests' in line:
                return line.strip()
        return "Duration not found"
    
    def parse_go_benchmarks(self, output: str) -> List[Dict]:
        """Parse Go benchmark results"""
        results = []
        lines = output.split('\n')
        
        for line in lines:
            if line.startswith('Benchmark'):
                parts = line.split()
                if len(parts) >= 4:
                    results.append({
                        "name": parts[0],
                        "iterations": parts[1],
                        "ns_per_op": parts[2],
                        "additional_metrics": parts[3:] if len(parts) > 3 else []
                    })
        
        return results
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        self.results['total_duration'] = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Summary section
        print(f"\n📊 SUMMARY")
        print(f"Total Duration: {self.results['total_duration']:.2f} seconds")
        
        # Go tests summary
        if self.results.get('go_tests'):
            print(f"\n🔵 GO TESTS")
            for package, result in self.results['go_tests'].items():
                status_emoji = "✅" if result.get('status') == 'passed' else "❌" if result.get('status') == 'failed' else "⚠️"
                print(f"  {status_emoji} {package}: {result.get('status', 'unknown')}")
                if result.get('coverage'):
                    print(f"    Coverage: {result['coverage']}")
        
        # Python tests summary
        if self.results.get('python_tests'):
            print(f"\n🐍 PYTHON UNIT TESTS")
            for test_name, result in self.results['python_tests'].items():
                status_emoji = "✅" if result.get('status') == 'passed' else "❌" if result.get('status') == 'failed' else "⚠️"
                print(f"  {status_emoji} {test_name}: {result.get('status', 'unknown')}")
        
        # Integration tests summary
        if self.results.get('integration_tests'):
            print(f"\n🔗 INTEGRATION TESTS")
            for test_name, result in self.results['integration_tests'].items():
                status_emoji = "✅" if result.get('status') == 'passed' else "❌" if result.get('status') == 'failed' else "⚠️"
                print(f"  {status_emoji} {test_name}: {result.get('status', 'unknown')}")
        
        # Performance tests summary
        if self.results.get('performance_tests'):
            print(f"\n🚀 PERFORMANCE TESTS")
            for test_name, result in self.results['performance_tests'].items():
                status_emoji = "✅" if result.get('status') == 'passed' else "❌" if result.get('status') == 'failed' else "⚠️"
                print(f"  {status_emoji} {test_name}: {result.get('status', 'unknown')}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            print(f"  • {rec}")
        
        # Save detailed report
        self.save_detailed_report()
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for failed tests
        failed_tests = []
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and result.get('status') == 'failed':
                        failed_tests.append(f"{category}.{test_name}")
        
        if failed_tests:
            recommendations.append(f"Fix failing tests: {', '.join(failed_tests)}")
        
        # Check for skipped tests
        skipped_tests = []
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and result.get('status') == 'skipped':
                        skipped_tests.append(f"{category}.{test_name}")
        
        if skipped_tests:
            recommendations.append(f"Investigate skipped tests: {', '.join(skipped_tests)}")
        
        # Performance recommendations
        if self.results.get('total_duration', 0) > 300:  # 5 minutes
            recommendations.append("Consider optimizing test performance - tests taking too long")
        
        # Coverage recommendations
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and result.get('coverage') and 'coverage:' in result['coverage']:
                        coverage_line = result['coverage']
                        # Extract coverage percentage if possible
                        if '%' in coverage_line:
                            coverage_str = coverage_line.split('%')[0].split()[-1]
                            try:
                                coverage_pct = float(coverage_str)
                                if coverage_pct < 80:
                                    recommendations.append(f"Improve test coverage for {test_name} (currently {coverage_pct}%)")
                            except ValueError:
                                pass
        
        if not recommendations:
            recommendations.append("All tests look good! Consider adding more edge case tests.")
        
        return recommendations
    
    def save_detailed_report(self):
        """Save detailed test report to file"""
        report_file = self.project_root / "test_report.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n📄 Detailed report saved to: {report_file}")
        
        except Exception as e:
            print(f"⚠ Failed to save detailed report: {e}")
    
    def run_all_tests(self):
        """Run all tests in the system"""
        print("🚀 Starting comprehensive test suite for Log Processing System")
        print(f"📁 Project root: {self.project_root}")
        
        # Run Go tests
        self.results['go_tests'] = self.run_go_tests()
        
        # Run Python unit tests
        self.results['python_tests'] = self.run_python_tests()
        
        # Run Python integration tests
        self.results['integration_tests'] = self.run_python_integration_tests()
        
        # Run logging functionality tests
        self.results['performance_tests'] = self.run_logging_functionality_tests()
        
        # Generate final report
        self.generate_test_report()
        
        # Return overall success status
        return self.calculate_overall_success()
    
    def calculate_overall_success(self) -> bool:
        """Calculate overall test success"""
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and result.get('status') == 'failed':
                        return False
        return True

def main():
    """Main function"""
    print("Log Processing System - Comprehensive Test Runner")
    print("=" * 60)
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
