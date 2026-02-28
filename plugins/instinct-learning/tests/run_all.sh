#!/bin/bash
# Run all tests for instinct-learning plugin
#
# Usage:
#   ./tests/run_all.sh              # Run all tests
#   ./tests/run_all.sh --verbose    # Run with verbose output
#   ./tests/run_all.sh --coverage   # Run with coverage report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PLUGIN_DIR"

VERBOSE=""
COVERAGE=""

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --coverage|-c)
            COVERAGE="1"
            shift
            ;;
    esac
done

echo "========================================"
echo "  Instinct-Learning Plugin Test Suite"
echo "========================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python: $PYTHON_VERSION"
echo ""

# Track test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .py)

    echo "Running: $test_name"
    echo "----------------------------------------"

    if [ -n "$COVERAGE" ]; then
        if python3 -m coverage run --append "$test_file" $VERBOSE; then
            ((PASSED_TESTS++))
            echo "✅ $test_name PASSED"
        else
            ((FAILED_TESTS++))
            echo "❌ $test_name FAILED"
        fi
    else
        if python3 "$test_file" $VERBOSE; then
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

# Run Python unit tests
echo "## Python Unit Tests"
echo ""

run_test "tests/test_instinct_cli.py"
run_test "tests/test_observe_sh.py"
run_test "tests/test_integration.py"

# Test hook script directly
echo "## Hook Script Tests"
echo ""

echo "Running: observe.sh syntax check"
if bash -n hooks/observe.sh; then
    echo "✅ observe.sh syntax OK"
    ((PASSED_TESTS++))
else
    echo "❌ observe.sh syntax error"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test CLI commands
echo "## CLI Command Tests"
echo ""

echo "Running: CLI help"
if python3 scripts/instinct_cli.py --help > /dev/null; then
    echo "✅ CLI help OK"
    ((PASSED_TESTS++))
else
    echo "❌ CLI help FAILED"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo "Running: CLI status command"
if python3 scripts/instinct_cli.py status > /dev/null; then
    echo "✅ CLI status OK"
    ((PASSED_TESTS++))
else
    echo "❌ CLI status FAILED"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""

# Coverage report
if [ -n "$COVERAGE" ]; then
    echo "## Coverage Report"
    echo ""
    python3 -m coverage report --include="scripts/*"
    echo ""
fi

# Summary
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
