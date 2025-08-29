#!/bin/bash
# Comprehensive Test Script for Log Processing System
# This script runs all tests and generates coverage reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GO_SERVICE_PATH="$PROJECT_ROOT/services/log-ingestion"
PYTHON_SERVICE_PATH="$PROJECT_ROOT/services/analytics"
REPORTS_DIR="$PROJECT_ROOT/test-reports"
COVERAGE_DIR="$PROJECT_ROOT/coverage"

# Create directories
mkdir -p "$REPORTS_DIR"
mkdir -p "$COVERAGE_DIR"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Log Processing System Test Suite   ${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAILED")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "INFO" "Checking prerequisites..."
    
    # Check Go
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version | awk '{print $3}')
        print_status "SUCCESS" "Go found: $GO_VERSION"
    else
        print_status "WARNING" "Go not found - Go tests will be skipped"
        GO_AVAILABLE=false
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_status "SUCCESS" "Python found: $PYTHON_VERSION"
        PYTHON_AVAILABLE=true
    else
        print_status "FAILED" "Python3 not found"
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_status "SUCCESS" "Docker found: $DOCKER_VERSION"
        DOCKER_AVAILABLE=true
    else
        print_status "WARNING" "Docker not found - integration tests may be limited"
        DOCKER_AVAILABLE=false
    fi
    
    echo ""
}

# Function to run Go tests
run_go_tests() {
    if [[ "$GO_AVAILABLE" != true ]]; then
        print_status "WARNING" "Skipping Go tests - Go not available"
        return 0
    fi
    
    print_status "INFO" "Running Go tests..."
    echo ""
    
    cd "$GO_SERVICE_PATH" || exit 1
    
    # Clean previous coverage files
    find . -name "coverage.out" -delete
    find . -name "*.test" -delete
    
    # Run tests with coverage for each package
    local packages=("." "./logger" "./middleware" "./handlers" "./database" "./models")
    local all_passed=true
    
    for package in "${packages[@]}"; do
        if [[ -d "$package" ]] && find "$package" -name "*_test.go" | grep -q .; then
            print_status "INFO" "Testing package: $package"
            
            # Generate coverage profile name
            local coverage_file="$COVERAGE_DIR/$(basename $package)_coverage.out"
            
            # Run tests
            if go test -v -cover -coverprofile="$coverage_file" "$package"; then
                print_status "SUCCESS" "Package $package tests passed"
                
                # Generate HTML coverage report
                if [[ -f "$coverage_file" ]]; then
                    go tool cover -html="$coverage_file" -o "$REPORTS_DIR/$(basename $package)_coverage.html"
                fi
            else
                print_status "FAILED" "Package $package tests failed"
                all_passed=false
            fi
            echo ""
        fi
    done
    
    # Run benchmarks
    print_status "INFO" "Running Go benchmarks..."
    if go test -bench=. -benchmem ./... > "$REPORTS_DIR/go_benchmarks.txt" 2>&1; then
        print_status "SUCCESS" "Go benchmarks completed"
    else
        print_status "WARNING" "Go benchmarks had issues"
    fi
    
    # Generate combined coverage report
    if find "$COVERAGE_DIR" -name "*_coverage.out" | grep -q .; then
        print_status "INFO" "Generating combined Go coverage report..."
        
        # Combine coverage files
        echo "mode: set" > "$COVERAGE_DIR/go_combined_coverage.out"
        grep -h -v "^mode:" "$COVERAGE_DIR"/*_coverage.out >> "$COVERAGE_DIR/go_combined_coverage.out" 2>/dev/null || true
        
        # Generate HTML report
        go tool cover -html="$COVERAGE_DIR/go_combined_coverage.out" -o "$REPORTS_DIR/go_combined_coverage.html"
        
        # Print coverage summary
        local coverage_pct=$(go tool cover -func="$COVERAGE_DIR/go_combined_coverage.out" | tail -1 | awk '{print $3}')
        print_status "SUCCESS" "Go coverage: $coverage_pct"
    fi
    
    cd "$PROJECT_ROOT"
    
    if [[ "$all_passed" == true ]]; then
        return 0
    else
        return 1
    fi
}

# Function to run Python tests
run_python_tests() {
    print_status "INFO" "Running Python tests..."
    echo ""
    
    cd "$PYTHON_SERVICE_PATH" || exit 1
    
    # Install test dependencies if requirements-test.txt exists
    if [[ -f "requirements-test.txt" ]]; then
        print_status "INFO" "Installing test dependencies..."
        pip3 install -r requirements-test.txt
    fi
    
    # Install main dependencies
    if [[ -f "requirements.txt" ]]; then
        print_status "INFO" "Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
    
    local all_passed=true
    
    # Run unit tests
    if [[ -f "test_structured_logger.py" ]]; then
        print_status "INFO" "Running structured logger tests..."
        if python3 test_structured_logger.py; then
            print_status "SUCCESS" "Structured logger tests passed"
        else
            print_status "FAILED" "Structured logger tests failed"
            all_passed=false
        fi
        echo ""
    fi
    
    # Run integration tests
    if [[ -f "test_integration.py" ]]; then
        print_status "INFO" "Running integration tests..."
        if python3 test_integration.py; then
            print_status "SUCCESS" "Integration tests passed"
        else
            print_status "FAILED" "Integration tests failed"
            all_passed=false
        fi
        echo ""
    fi
    
    # Run with coverage if available
    if command -v coverage &> /dev/null; then
        print_status "INFO" "Running Python tests with coverage..."
        
        # Run coverage
        coverage run --source=. -m unittest discover -v > "$REPORTS_DIR/python_tests.txt" 2>&1 || true
        
        # Generate reports
        coverage report > "$REPORTS_DIR/python_coverage.txt" 2>&1 || true
        coverage html -d "$REPORTS_DIR/python_coverage_html" 2>&1 || true
        
        # Print coverage summary
        local coverage_pct=$(coverage report --show-missing | tail -1 | awk '{print $4}' | sed 's/%//')
        if [[ "$coverage_pct" =~ ^[0-9]+$ ]]; then
            print_status "SUCCESS" "Python coverage: ${coverage_pct}%"
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    if [[ "$all_passed" == true ]]; then
        return 0
    else
        return 1
    fi
}

# Function to run logging functionality tests
run_logging_tests() {
    print_status "INFO" "Running logging functionality tests..."
    echo ""
    
    if [[ -f "$PROJECT_ROOT/test_logging.py" ]]; then
        if python3 "$PROJECT_ROOT/test_logging.py"; then
            print_status "SUCCESS" "Logging functionality tests passed"
            return 0
        else
            print_status "FAILED" "Logging functionality tests failed"
            return 1
        fi
    else
        print_status "WARNING" "Logging functionality test file not found"
        return 0
    fi
}

# Function to run integration tests with Docker
run_docker_integration_tests() {
    if [[ "$DOCKER_AVAILABLE" != true ]]; then
        print_status "WARNING" "Skipping Docker integration tests - Docker not available"
        return 0
    fi
    
    print_status "INFO" "Running Docker integration tests..."
    echo ""
    
    # Check if docker-compose.yml exists
    if [[ -f "$PROJECT_ROOT/docker/docker-compose.yml" ]]; then
        cd "$PROJECT_ROOT/docker" || exit 1
        
        # Start services in background
        print_status "INFO" "Starting Docker services..."
        if docker-compose up -d --build; then
            print_status "SUCCESS" "Docker services started"
            
            # Wait for services to be ready
            sleep 10
            
            # Run basic health checks
            print_status "INFO" "Running health checks..."
            
            # Check if log ingestion service is responding
            if curl -f http://localhost:8080/health &> /dev/null; then
                print_status "SUCCESS" "Log ingestion service is healthy"
            else
                print_status "WARNING" "Log ingestion service health check failed"
            fi
            
            # Cleanup
            print_status "INFO" "Cleaning up Docker services..."
            docker-compose down -v
            
        else
            print_status "FAILED" "Failed to start Docker services"
            return 1
        fi
        
        cd "$PROJECT_ROOT"
    else
        print_status "WARNING" "Docker compose file not found"
    fi
    
    return 0
}

# Function to generate summary report
generate_summary_report() {
    local go_result=$1
    local python_result=$2
    local logging_result=$3
    local docker_result=$4
    
    print_status "INFO" "Generating summary report..."
    
    local report_file="$REPORTS_DIR/test_summary.txt"
    
    cat > "$report_file" << EOF
Log Processing System - Test Summary Report
Generated: $(date)
==========================================

Test Results:
- Go Tests: $([ $go_result -eq 0 ] && echo "PASSED" || echo "FAILED")
- Python Tests: $([ $python_result -eq 0 ] && echo "PASSED" || echo "FAILED")
- Logging Tests: $([ $logging_result -eq 0 ] && echo "PASSED" || echo "FAILED")
- Docker Integration: $([ $docker_result -eq 0 ] && echo "PASSED" || echo "FAILED")

Coverage Reports:
- Go Coverage: $REPORTS_DIR/go_combined_coverage.html
- Python Coverage: $REPORTS_DIR/python_coverage_html/index.html

Detailed Reports:
- Go Benchmarks: $REPORTS_DIR/go_benchmarks.txt
- Python Tests: $REPORTS_DIR/python_tests.txt
- Python Coverage: $REPORTS_DIR/python_coverage.txt

Recommendations:
EOF

    # Add recommendations based on results
    if [[ $go_result -ne 0 ]]; then
        echo "- Fix failing Go tests" >> "$report_file"
    fi
    
    if [[ $python_result -ne 0 ]]; then
        echo "- Fix failing Python tests" >> "$report_file"
    fi
    
    if [[ $logging_result -ne 0 ]]; then
        echo "- Fix logging functionality issues" >> "$report_file"
    fi
    
    if [[ $docker_result -ne 0 ]]; then
        echo "- Check Docker integration setup" >> "$report_file"
    fi
    
    if [[ $go_result -eq 0 && $python_result -eq 0 && $logging_result -eq 0 ]]; then
        echo "- All tests passed! Consider adding more edge case tests." >> "$report_file"
    fi
    
    print_status "SUCCESS" "Summary report generated: $report_file"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Check prerequisites
    check_prerequisites
    
    # Initialize results
    local go_result=0
    local python_result=0
    local logging_result=0
    local docker_result=0
    
    # Run tests
    run_go_tests || go_result=$?
    run_python_tests || python_result=$?
    run_logging_tests || logging_result=$?
    run_docker_integration_tests || docker_result=$?
    
    # Calculate total time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Generate summary
    generate_summary_report $go_result $python_result $logging_result $docker_result
    
    # Final summary
    echo ""
    print_status "INFO" "Test suite completed in ${duration} seconds"
    print_status "INFO" "Reports available in: $REPORTS_DIR"
    
    # Determine overall result
    if [[ $go_result -eq 0 && $python_result -eq 0 && $logging_result -eq 0 ]]; then
        print_status "SUCCESS" "All critical tests passed!"
        echo ""
        echo -e "${GREEN}🎉 Test suite completed successfully!${NC}"
        exit 0
    else
        print_status "FAILED" "Some tests failed. Check reports for details."
        echo ""
        echo -e "${RED}💥 Test suite completed with failures.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
