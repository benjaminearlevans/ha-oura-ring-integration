#!/usr/bin/env python3
"""Test runner for Oura Ring integration."""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the test suite."""
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    print("🧪 Running Oura Ring Integration Tests...")
    print("=" * 50)
    
    # Install test requirements if needed
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True, capture_output=True)
        print("✅ Test dependencies installed")
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Could not install test dependencies")
    
    # Run pytest
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--cov=custom_components.oura_full",
            "--cov-report=term-missing"
        ], cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
        
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest first:")
        print("   pip install pytest pytest-asyncio pytest-cov")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
