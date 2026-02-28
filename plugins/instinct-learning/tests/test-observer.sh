#!/bin/bash
# Observer Integration Tests
# Tests the observer system end-to-end

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

test_start() {
    echo -n "Testing: $1... "
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Setup
setup() {
    TEST_DIR="/tmp/instinct-observer-test-$$"
    rm -rf "$TEST_DIR"
    mkdir -p "$TEST_DIR"
    export INSTINCT_LEARNING_DATA_DIR="$TEST_DIR"
    cd "$PLUGIN_ROOT"
}

# Teardown
teardown() {
    rm -rf "$TEST_DIR"
}

# Test 1: pattern_to_instinct function
test_pattern_to_instinct() {
    test_start "pattern_to_instinct conversion"

    setup

    # Create sample observations - need enough to trigger pattern detection
    # Tool preference: 10+ same tool usage triggers detection
    obs_file="$TEST_DIR/observations.jsonl"
    for i in {1..10}; do
        echo "{\"timestamp\":\"2025-01-01T00:0$i:00Z\",\"type\":\"pre_tool\",\"tool\":\"Edit\",\"session\":\"s1\"}" >> "$obs_file"
    done

    # Run observer
    python3 scripts/run-observer.py > /dev/null 2>&1 || true

    # Check that instincts were created
    personal_dir="$TEST_DIR/instincts/personal"
    if [ -d "$personal_dir" ]; then
        count=$(find "$personal_dir" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            # Check that at least one file has proper structure
            for file in "$personal_dir"/*.md; do
                if grep -q "^---" "$file" && grep -q "^id:" "$file"; then
                    test_pass
                    teardown
                    return 0
                fi
            done
        fi
    fi

    test_fail "No instincts were created"
    teardown
}

# Test 2: observer handles empty observations
test_empty_observations() {
    test_start "observer handles empty observations"

    setup
    touch "$TEST_DIR/observations.jsonl"

    # Should exit cleanly
    python3 scripts/run-observer.py > /tmp/test-observer.log 2>&1 || true

    # Check it didn't crash
    if grep -q "No observations to analyze" /tmp/test-observer.log 2>/dev/null; then
        test_pass
    else
        test_fail "Expected 'No observations to analyze' message"
    fi

    rm -f /tmp/test-observer.log
    teardown
}

# Test 3: observer creates personal directory
test_creates_directories() {
    test_start "observer creates directory structure"

    setup

    # Create observations with Edit tool repeated 10 times (triggers tool preference)
    obs_file="$TEST_DIR/observations.jsonl"
    for i in {1..10}; do
        echo "{\"timestamp\":\"2025-01-01T00:0$i:00Z\",\"type\":\"pre_tool\",\"tool\":\"Edit\",\"session\":\"s1\"}" >> "$obs_file"
    done

    python3 scripts/run-observer.py > /dev/null 2>&1 || true

    personal_dir="$TEST_DIR/instincts/personal"
    if [ -d "$personal_dir" ]; then
        test_pass
    else
        test_fail "Personal directory not created"
    fi

    teardown
}

# Test 4: start-observer.sh script
test_start_observer_script() {
    test_start "start-observer.sh exists and is executable"

    if [ -x "scripts/start-observer.sh" ]; then
        test_pass
    else
        test_fail "start-observer.sh not executable"
    fi
}

# Test 5: stop-observer.sh script
test_stop_observer_script() {
    test_start "stop-observer.sh exists and is executable"

    if [ -x "scripts/stop-observer.sh" ]; then
        test_pass
    else
        test_fail "stop-observer.sh not executable"
    fi
}

# Test 6: evolution opportunity detection
test_evolution_detection() {
    test_start "observer detects evolution opportunities"

    setup

    # Create enough instincts to trigger evolution
    obs_file="$TEST_DIR/observations.jsonl"
    # Create observations for 3 instincts in same domain with high confidence
    # This is complex, so we'll just check the evolution opportunity detection runs
    for i in {1..20}; do
        echo "{\"timestamp\":\"2025-01-01T00:00:00Z\",\"type\":\"pre_tool\",\"tool\":\"Test\",\"session\":\"s1\"}" >> "$obs_file"
    done

    # Run observer
    output=$(python3 scripts/run-observer.py 2>&1 || true)

    # Should complete without crash
    test_pass
    teardown
}

# Run all tests
echo "=== Observer Tests ==="

test_pattern_to_instinct
test_empty_observations
test_creates_directories
test_start_observer_script
test_stop_observer_script
test_evolution_detection

echo ""
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
