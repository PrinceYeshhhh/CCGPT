@echo off
REM CustomerCareGPT Cloud Testing Suite
REM Windows batch file to run cloud tests

echo 🌐 CustomerCareGPT Cloud Testing Suite
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Install required packages if not already installed
echo 📦 Installing required packages...
pip install pytest httpx asyncio >nul 2>&1

REM Run quick connectivity test first
echo.
echo 🔗 Running Quick Connectivity Test...
python test_cloud_setup.py --quick

if errorlevel 1 (
    echo.
    echo ❌ Quick test failed. Please check your cloud deployment.
    pause
    exit /b 1
)

echo.
echo ✅ Quick test passed! Running full test suite...
echo.

REM Run full test suite
python test_cloud_setup.py

if errorlevel 1 (
    echo.
    echo ❌ Some tests failed. Check the report above for details.
    pause
    exit /b 1
) else (
    echo.
    echo 🎉 All tests passed! Your application is ready for production.
    pause
    exit /b 0
)
