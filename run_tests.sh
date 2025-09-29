#!/bin/bash
# CustomerCareGPT Cloud Testing Suite
# Linux/Mac shell script to run cloud tests

set -e

echo "🌐 CustomerCareGPT Cloud Testing Suite"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python3 and try again"
    exit 1
fi

# Install required packages if not already installed
echo "📦 Installing required packages..."
pip3 install pytest httpx asyncio > /dev/null 2>&1

# Run quick connectivity test first
echo ""
echo "🔗 Running Quick Connectivity Test..."
python3 test_cloud_setup.py --quick

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Quick test failed. Please check your cloud deployment."
    exit 1
fi

echo ""
echo "✅ Quick test passed! Running full test suite..."
echo ""

# Run full test suite
python3 test_cloud_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Some tests failed. Check the report above for details."
    exit 1
else
    echo ""
    echo "🎉 All tests passed! Your application is ready for production."
    exit 0
fi
