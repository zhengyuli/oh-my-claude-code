#!/bin/bash
# Run all tests for instinct-learning plugin
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PLUGIN_DIR"

VERBOSE=""
COVERAGE=""
TEST_TYPE="all"

for arg in "$@"; do
    case $arg in
        --verbose|-v) VERBOSE="-v" ;;
        --coverage|-c) COVERAGE="1" ;;
        --unit) TEST_TYPE="unit" ;;
        --integration) TEST_TYPE="integration" ;;
        --scenario) TEST_TYPE="scenario" ;;
    esac
done

echo "========================================"
echo "  Instinct-Learning Plugin Test Suite"
echo "========================================"
echo ""

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python: $PYTHON_VERSION"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_path="$1"
    local test_name=$(basename "$test_path" .py)

    echo "Running: $test_name"
    echo "----------------------------------------"

    if [ -n "$COVERAGE" ]; then
        if python3 -m pytest "$test_path" $VERBOSE --cov=scripts --cov-report=term-missing; then
            ((PASSED_TESTS++))
            echo "✅ $test_name PASSED"
        else
            ((FAILED_TESTS++))
            echo "❌ $test_name FAILED"
        fi
    else
        if python3 -m pytest "$test_path" $VERBOSE; then
            ((PASSED_TESTS++))
            echo "✅ $test_name PASSED"
        else
            ((FAILED_TESTS++))
            echo "❌ $test_name FAILED"
        fi
    fi

    ((TOTAL_TESTS++))
    echo ""
}

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo "## Unit Tests"
        echo ""
        for test_file in tests/unit/test_*.py; do
            run_test "$test_file"
        done
        ;;
    integration)
        echo "## Integration Tests"
        echo ""
        for test_file in tests/integration/test_*.py; do
            run_test "$test_file"
        done
        ;;
    scenario)
        echo "## Scenario Tests"
        echo ""
        for test_file in tests/scenarios/test_*.py; do
            run_test "$test_file"
        done
        ;;
    all)
        echo "## All Tests"
        echo ""
        for test_file in tests/unit/test_*.py tests/integration/test_*.py tests/scenarios/test_*.py; do
            run_test "$test_file"
        done
        ;;
esac

echo "========================================"
echo "  Test Summary"
echo "========================================"
echo "  Total:  $TOTAL_TESTS"
echo "  Passed: $PASSED_TESTS"
echo "  Failed: $FAILED_TESTS"
echo "========================================"

if [ $FAILED_TESTS -gt 0 ]; then
    echo "❌ Some tests failed"
    exit 1
else
    echo "✅ All tests passed"
    exit 0
fi
