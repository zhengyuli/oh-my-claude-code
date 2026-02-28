#!/bin/bash
# Run all tests with detailed output
# Usage: ./tests/run-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PLUGIN_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Instinct Learning - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to run a test file
run_test_file() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .py)

    echo -e "${BLUE}Running: ${test_name}${NC}"
    echo ""

    # Run with verbose mode
    if output=$(python3 "$test_file" -v 2>&1); then
        # Extract test count
        passed=$(echo "$output" | grep -o 'Ran [0-9]* test' | grep -o '[0-9]*')
        TOTAL_TESTS=$((TOTAL_TESTS + passed))
        TOTAL_PASSED=$((TOTAL_PASSED + passed))

        # Show summary lines
        echo "$output" | grep -E "test_|Ran|OK|FAIL" | tail -10
        echo -e "${GREEN}✓ ${test_name}: ${passed} tests passed${NC}"
    else
        # Get counts
        passed=$(echo "$output" | grep -o 'Ran [0-9]* test' | grep -o '[0-9]*' || echo "0")
        failed=$(echo "$output" | grep -o 'FAILED (failures=[0-9]*)' | grep -o '[0-9]*' || echo "0")
        TOTAL_TESTS=$((TOTAL_TESTS + passed + failed))
        TOTAL_PASSED=$((TOTAL_PASSED + passed))
        TOTAL_FAILED=$((TOTAL_FAILED + failed))

        echo "$output" | grep -E "FAIL|ERROR" | head -20
        echo -e "${RED}✗ ${test_name}: ${failed} tests failed${NC}"
    fi
    echo ""
}

# Run hook tests
echo -e "${BLUE}=== Hook Tests ===${NC}"
if ./tests/test-hooks.sh 2>&1; then
    TOTAL_PASSED=$((TOTAL_PASSED + 5))
    TOTAL_TESTS=$((TOTAL_TESTS + 5))
    echo -e "${GREEN}✓ Hook Tests: 5/5 passed${NC}"
else
    TOTAL_FAILED=$((TOTAL_FAILED + 5))
    TOTAL_TESTS=$((TOTAL_TESTS + 5))
    echo -e "${RED}✗ Hook Tests: FAILED${NC}"
fi
echo ""

# Run observer tests
echo -e "${BLUE}=== Observer Tests ===${NC}"
if ./tests/test-observer.sh 2>&1; then
    TOTAL_PASSED=$((TOTAL_PASSED + 6))
    TOTAL_TESTS=$((TOTAL_TESTS + 6))
    echo -e "${GREEN}✓ Observer Tests: 6/6 passed${NC}"
else
    TOTAL_FAILED=$((TOTAL_FAILED + 6))
    TOTAL_TESTS=$((TOTAL_TESTS + 6))
    echo -e "${RED}✗ Observer Tests: FAILED${NC}"
fi
echo ""

# Run session-memory tests
echo -e "${BLUE}=== Session Memory Tests ===${NC}"
if ./tests/test-session-memory.sh 2>&1; then
    TOTAL_PASSED=$((TOTAL_PASSED + 6))
    TOTAL_TESTS=$((TOTAL_TESTS + 6))
    echo -e "${GREEN}✓ Session Memory Tests: 6/6 passed${NC}"
else
    TOTAL_FAILED=$((TOTAL_FAILED + 6))
    TOTAL_TESTS=$((TOTAL_TESTS + 6))
    echo -e "${RED}✗ Session Memory Tests: FAILED${NC}"
fi
echo ""

# Run Python test files
for test_file in tests/test-*.py; do
    run_test_file "$test_file"
done

# Final summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "Passed: ${GREEN}${TOTAL_PASSED}${NC}"
if [ $TOTAL_FAILED -gt 0 ]; then
    echo -e "Failed: ${RED}${TOTAL_FAILED}${NC}"
    echo ""
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "Failed: 0"
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
fi
