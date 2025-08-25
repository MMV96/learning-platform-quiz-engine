#!/usr/bin/env python3
"""
Test runner script for the Quiz Engine microservice.
Runs the complete test suite with coverage reporting.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite with pytest."""
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if test requirements are installed
    try:
        import pytest
    except ImportError:
        print("pytest not found. Installing test requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "test-requirements.txt"])
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "--disable-warnings",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--asyncio-mode=auto"
    ]
    
    # Add any additional arguments passed to this script
    cmd.extend(sys.argv[1:])
    
    print("Running Quiz Engine tests...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        
        print("\n" + "="*50)
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("❌ Some tests failed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        print("="*50)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)