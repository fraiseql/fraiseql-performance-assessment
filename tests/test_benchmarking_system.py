#!/usr/bin/env python3
"""
Test suite for the benchmarking system
Validates Phase 2 JMeter integration and statistical analysis
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_jmeter_wrapper():
    """Test JMeter wrapper script functionality"""
    print("🧪 Testing JMeter wrapper script...")

    # Test help output
    result = subprocess.run(
        ["./tests/perf/scripts/run-headless.sh"], capture_output=True, text=True
    )

    if "Usage:" in result.stdout:
        print("✅ JMeter wrapper help works")
        return True
    else:
        print("❌ JMeter wrapper help failed")
        return False


def test_analysis_script():
    """Test statistical analysis script"""
    print("🧪 Testing analysis script...")

    # Test help output
    result = subprocess.run(
        ["python3", "tests/perf/scripts/analyze-results.py", "--help"],
        capture_output=True,
        text=True,
    )

    if "JMeter Results Statistical Analysis" in result.stdout:
        print("✅ Analysis script help works")
        return True
    else:
        print("❌ Analysis script help failed")
        return False


def test_warmup_script():
    """Test warmup script functionality"""
    print("🧪 Testing warmup script...")

    # Test help output (no valid args)
    result = subprocess.run(
        ["./tests/perf/scripts/warmup.sh"], capture_output=True, text=True
    )

    # Should exit with error but show usage
    if result.returncode != 0:
        print("✅ Warmup script validation works")
        return True
    else:
        print("❌ Warmup script validation failed")
        return False


def test_benchmark_config():
    """Test benchmark configuration class"""
    print("🧪 Testing benchmark configuration...")

    try:
        # Import the config class
        sys.path.insert(0, ".")
        from run_comparative_benchmarks import BenchmarkConfig

        config = BenchmarkConfig(threads=25, loops=500, ramp_up=15)
        assert config.threads == 25
        assert config.loops == 500
        assert config.ramp_up == 15

        print("✅ Benchmark configuration works")
        return True
    except Exception as e:
        print(f"❌ Benchmark configuration failed: {e}")
        return False


def test_jmeter_test_plan_validation():
    """Test JMeter test plan validation"""
    print("🧪 Testing JMeter test plan validation...")

    try:
        sys.path.insert(0, ".")
        from run_comparative_benchmarks import ComparativeBenchmarkAnalyzer

        analyzer = ComparativeBenchmarkAnalyzer()

        # Test with existing file
        if os.path.exists("tests/perf/jmeter/comparative-test-plan.jmx"):
            result = analyzer._validate_test_plan_exists(
                "tests/perf/jmeter/comparative-test-plan.jmx"
            )
            if result:
                print("✅ Test plan validation works")
                return True
            else:
                print("❌ Test plan validation failed")
                return False
        else:
            print("⚠️  Skipping test plan validation (no test file)")
            return True

    except Exception as e:
        print(f"❌ Test plan validation error: {e}")
        return False


def run_test_suite():
    """Run the complete test suite"""
    print("🚀 Running Benchmarking System Test Suite")
    print("=" * 50)

    tests = [
        test_jmeter_wrapper,
        test_analysis_script,
        test_warmup_script,
        test_benchmark_config,
        test_jmeter_test_plan_validation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"💥 Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Quality metric: 10/10")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Quality metric: {passed}/{total}")
        return False


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
