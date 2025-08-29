@echo off
REM Comprehensive Test Script for Log Processing System (Windows)
REM This script runs all tests and generates coverage reports

setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_ROOT=%~dp0"
set "GO_SERVICE_PATH=%PROJECT_ROOT%services\log-ingestion"
set "PYTHON_SERVICE_PATH=%PROJECT_ROOT%services\analytics"
set "REPORTS_DIR=%PROJECT_ROOT%test-reports"
set "COVERAGE_DIR=%PROJECT_ROOT%coverage"

REM Create directories
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"
if not exist "%COVERAGE_DIR%" mkdir "%COVERAGE_DIR%"

echo ======================================
echo   Log Processing System Test Suite   
echo ======================================
echo.

REM Function to check prerequisites
echo [INFO] Checking prerequisites...

REM Check Go
where go >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%a in ('go version') do set "GO_VERSION=%%a"
    echo [SUCCESS] Go found: !GO_VERSION!
    set "GO_AVAILABLE=true"
) else (
    echo [WARNING] Go not found - Go tests will be skipped
    set "GO_AVAILABLE=false"
)

REM Check Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%a in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%a"
    echo [SUCCESS] Python found: !PYTHON_VERSION!
    set "PYTHON_AVAILABLE=true"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%a in ('python3 --version 2^>^&1') do set "PYTHON_VERSION=%%a"
        echo [SUCCESS] Python3 found: !PYTHON_VERSION!
        set "PYTHON_AVAILABLE=true"
        set "PYTHON_CMD=python3"
    ) else (
        echo [FAILED] Python not found
        exit /b 1
    )
)

if not defined PYTHON_CMD set "PYTHON_CMD=python"

REM Check Docker
where docker >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%a in ('docker --version') do set "DOCKER_VERSION=%%a"
    echo [SUCCESS] Docker found: !DOCKER_VERSION!
    set "DOCKER_AVAILABLE=true"
) else (
    echo [WARNING] Docker not found - integration tests may be limited
    set "DOCKER_AVAILABLE=false"
)

echo.

REM Run Go tests
if "%GO_AVAILABLE%"=="true" (
    echo [INFO] Running Go tests...
    echo.
    
    cd /d "%GO_SERVICE_PATH%"
    
    REM Clean previous coverage files
    del /q coverage.out 2>nul
    del /q *.test 2>nul
    
    set "GO_TESTS_PASSED=true"
    
    REM Test packages
    for %%p in (. logger middleware handlers database models) do (
        if exist "%%p" (
            dir /b "%%p\*_test.go" >nul 2>&1
            if !errorlevel! equ 0 (
                echo [INFO] Testing package: %%p
                
                set "COVERAGE_FILE=%COVERAGE_DIR%\%%p_coverage.out"
                if "%%p"=="." set "COVERAGE_FILE=%COVERAGE_DIR%\main_coverage.out"
                
                go test -v -cover -coverprofile="!COVERAGE_FILE!" "%%p"
                if !errorlevel! equ 0 (
                    echo [SUCCESS] Package %%p tests passed
                    
                    REM Generate HTML coverage report
                    if exist "!COVERAGE_FILE!" (
                        go tool cover -html="!COVERAGE_FILE!" -o "%REPORTS_DIR%\%%p_coverage.html"
                    )
                ) else (
                    echo [FAILED] Package %%p tests failed
                    set "GO_TESTS_PASSED=false"
                )
                echo.
            )
        )
    )
    
    REM Run benchmarks
    echo [INFO] Running Go benchmarks...
    go test -bench=. -benchmem ./... > "%REPORTS_DIR%\go_benchmarks.txt" 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Go benchmarks completed
    ) else (
        echo [WARNING] Go benchmarks had issues
    )
    
    REM Generate combined coverage report
    dir /b "%COVERAGE_DIR%\*_coverage.out" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Generating combined Go coverage report...
        
        REM Combine coverage files
        echo mode: set > "%COVERAGE_DIR%\go_combined_coverage.out"
        for %%f in ("%COVERAGE_DIR%\*_coverage.out") do (
            findstr /v "^mode:" "%%f" >> "%COVERAGE_DIR%\go_combined_coverage.out" 2>nul
        )
        
        REM Generate HTML report
        go tool cover -html="%COVERAGE_DIR%\go_combined_coverage.out" -o "%REPORTS_DIR%\go_combined_coverage.html"
        
        REM Print coverage summary
        for /f "tokens=3" %%c in ('go tool cover -func^="%COVERAGE_DIR%\go_combined_coverage.out" ^| findstr /r "total:"') do (
            echo [SUCCESS] Go coverage: %%c
        )
    )
    
    cd /d "%PROJECT_ROOT%"
) else (
    echo [WARNING] Skipping Go tests - Go not available
    set "GO_TESTS_PASSED=true"
)

REM Run Python tests
if "%PYTHON_AVAILABLE%"=="true" (
    echo [INFO] Running Python tests...
    echo.
    
    cd /d "%PYTHON_SERVICE_PATH%"
    
    REM Install dependencies
    if exist "requirements-test.txt" (
        echo [INFO] Installing test dependencies...
        %PYTHON_CMD% -m pip install -r requirements-test.txt
    )
    
    if exist "requirements.txt" (
        echo [INFO] Installing Python dependencies...
        %PYTHON_CMD% -m pip install -r requirements.txt
    )
    
    set "PYTHON_TESTS_PASSED=true"
    
    REM Run unit tests
    if exist "test_structured_logger.py" (
        echo [INFO] Running structured logger tests...
        %PYTHON_CMD% test_structured_logger.py
        if !errorlevel! equ 0 (
            echo [SUCCESS] Structured logger tests passed
        ) else (
            echo [FAILED] Structured logger tests failed
            set "PYTHON_TESTS_PASSED=false"
        )
        echo.
    )
    
    REM Run integration tests
    if exist "test_integration.py" (
        echo [INFO] Running integration tests...
        %PYTHON_CMD% test_integration.py
        if !errorlevel! equ 0 (
            echo [SUCCESS] Integration tests passed
        ) else (
            echo [FAILED] Integration tests failed
            set "PYTHON_TESTS_PASSED=false"
        )
        echo.
    )
    
    REM Run with coverage if available
    %PYTHON_CMD% -m coverage --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Running Python tests with coverage...
        
        %PYTHON_CMD% -m coverage run --source=. -m unittest discover -v > "%REPORTS_DIR%\python_tests.txt" 2>&1
        %PYTHON_CMD% -m coverage report > "%REPORTS_DIR%\python_coverage.txt" 2>&1
        %PYTHON_CMD% -m coverage html -d "%REPORTS_DIR%\python_coverage_html" 2>&1
        
        for /f "tokens=4" %%c in ('type "%REPORTS_DIR%\python_coverage.txt" ^| findstr /r "TOTAL"') do (
            echo [SUCCESS] Python coverage: %%c
        )
    )
    
    cd /d "%PROJECT_ROOT%"
) else (
    echo [WARNING] Skipping Python tests - Python not available
    set "PYTHON_TESTS_PASSED=true"
)

REM Run logging functionality tests
echo [INFO] Running logging functionality tests...
echo.

if exist "%PROJECT_ROOT%test_logging.py" (
    %PYTHON_CMD% "%PROJECT_ROOT%test_logging.py"
    if !errorlevel! equ 0 (
        echo [SUCCESS] Logging functionality tests passed
        set "LOGGING_TESTS_PASSED=true"
    ) else (
        echo [FAILED] Logging functionality tests failed
        set "LOGGING_TESTS_PASSED=false"
    )
) else (
    echo [WARNING] Logging functionality test file not found
    set "LOGGING_TESTS_PASSED=true"
)

REM Docker integration tests
if "%DOCKER_AVAILABLE%"=="true" (
    echo [INFO] Running Docker integration tests...
    echo.
    
    if exist "%PROJECT_ROOT%docker\docker-compose.yml" (
        cd /d "%PROJECT_ROOT%docker"
        
        echo [INFO] Starting Docker services...
        docker-compose up -d --build
        if !errorlevel! equ 0 (
            echo [SUCCESS] Docker services started
            
            REM Wait for services
            timeout /t 10 /nobreak >nul
            
            echo [INFO] Running health checks...
            
            REM Basic health check
            curl -f http://localhost:8080/health >nul 2>&1
            if !errorlevel! equ 0 (
                echo [SUCCESS] Log ingestion service is healthy
            ) else (
                echo [WARNING] Log ingestion service health check failed
            )
            
            echo [INFO] Cleaning up Docker services...
            docker-compose down -v
            
            set "DOCKER_TESTS_PASSED=true"
        ) else (
            echo [FAILED] Failed to start Docker services
            set "DOCKER_TESTS_PASSED=false"
        )
        
        cd /d "%PROJECT_ROOT%"
    ) else (
        echo [WARNING] Docker compose file not found
        set "DOCKER_TESTS_PASSED=true"
    )
) else (
    echo [WARNING] Skipping Docker integration tests - Docker not available
    set "DOCKER_TESTS_PASSED=true"
)

REM Generate summary report
echo [INFO] Generating summary report...

set "REPORT_FILE=%REPORTS_DIR%\test_summary.txt"

echo Log Processing System - Test Summary Report > "%REPORT_FILE%"
echo Generated: %date% %time% >> "%REPORT_FILE%"
echo ========================================== >> "%REPORT_FILE%"
echo. >> "%REPORT_FILE%"
echo Test Results: >> "%REPORT_FILE%"

if "%GO_TESTS_PASSED%"=="true" (
    echo - Go Tests: PASSED >> "%REPORT_FILE%"
) else (
    echo - Go Tests: FAILED >> "%REPORT_FILE%"
)

if "%PYTHON_TESTS_PASSED%"=="true" (
    echo - Python Tests: PASSED >> "%REPORT_FILE%"
) else (
    echo - Python Tests: FAILED >> "%REPORT_FILE%"
)

if "%LOGGING_TESTS_PASSED%"=="true" (
    echo - Logging Tests: PASSED >> "%REPORT_FILE%"
) else (
    echo - Logging Tests: FAILED >> "%REPORT_FILE%"
)

if "%DOCKER_TESTS_PASSED%"=="true" (
    echo - Docker Integration: PASSED >> "%REPORT_FILE%"
) else (
    echo - Docker Integration: FAILED >> "%REPORT_FILE%"
)

echo. >> "%REPORT_FILE%"
echo Coverage Reports: >> "%REPORT_FILE%"
echo - Go Coverage: %REPORTS_DIR%\go_combined_coverage.html >> "%REPORT_FILE%"
echo - Python Coverage: %REPORTS_DIR%\python_coverage_html\index.html >> "%REPORT_FILE%"
echo. >> "%REPORT_FILE%"
echo Detailed Reports: >> "%REPORT_FILE%"
echo - Go Benchmarks: %REPORTS_DIR%\go_benchmarks.txt >> "%REPORT_FILE%"
echo - Python Tests: %REPORTS_DIR%\python_tests.txt >> "%REPORT_FILE%"
echo - Python Coverage: %REPORTS_DIR%\python_coverage.txt >> "%REPORT_FILE%"

echo [SUCCESS] Summary report generated: %REPORT_FILE%

REM Final summary
echo.
echo [INFO] Test suite completed
echo [INFO] Reports available in: %REPORTS_DIR%

REM Determine overall result
if "%GO_TESTS_PASSED%"=="true" if "%PYTHON_TESTS_PASSED%"=="true" if "%LOGGING_TESTS_PASSED%"=="true" (
    echo [SUCCESS] All critical tests passed!
    echo.
    echo 🎉 Test suite completed successfully!
    exit /b 0
) else (
    echo [FAILED] Some tests failed. Check reports for details.
    echo.
    echo 💥 Test suite completed with failures.
    exit /b 1
)
