#!/bin/bash
# Hook Tests for instinct-learning plugin
# Run with: ./tests/test-hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="/tmp/instinct-learning-test-$$"
DATA_DIR="$TEST_DIR/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test functions
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

assert_equals() {
    if [ "$1" = "$2" ]; then
        return 0
    else
        test_fail "Expected '$2', got '$1'"
        return 1
    fi
}

assert_file_exists() {
    if [ -f "$1" ]; then
        return 0
    else
        test_fail "File does not exist: $1"
        return 1
    fi
}

assert_file_contains() {
    if grep -q "$2" "$1" 2>/dev/null; then
        return 0
    else
        test_fail "File does not contain: $2"
        return 1
    fi
}

# Setup
setup() {
    rm -rf "$TEST_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/instincts/personal"
    mkdir -p "$DATA_DIR/instincts/shared"
    export INSTINCT_LEARNING_DATA_DIR="$DATA_DIR"
    export CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT"
    export CLAUDE_SESSION_ID="test-session-$$"
}

# Teardown
teardown() {
    rm -rf "$TEST_DIR"
}

# Test: pre-tool hook creates observation
test_pre_tool_hook() {
    test_start "pre-tool.sh creates observation record"

    setup

    export CLAUDE_TOOL_NAME="Edit"
    export CLAUDE_TOOL_INPUT="test input"

    "$PLUGIN_ROOT/hooks/pre-tool.sh"

    # Wait for async execution
    sleep 1

    assert_file_exists "$DATA_DIR/observations.jsonl"
    assert_file_contains "$DATA_DIR/observations.jsonl" "Edit"
    assert_file_contains "$DATA_DIR/observations.jsonl" "pre_tool"

    test_pass
    teardown
}

# Test: post-tool hook creates observation
test_post_tool_hook() {
    test_start "post-tool.sh creates observation record"

    setup

    export CLAUDE_TOOL_NAME="Write"
    export CLAUDE_TOOL_INPUT="test input"
    export CLAUDE_EXIT_CODE="0"

    echo "test response" | "$PLUGIN_ROOT/hooks/post-tool.sh"

    # Wait for async execution
    sleep 1

    assert_file_exists "$DATA_DIR/observations.jsonl"
    assert_file_contains "$DATA_DIR/observations.jsonl" "Write"
    assert_file_contains "$DATA_DIR/observations.jsonl" "post_tool"

    test_pass
    teardown
}

# Test: stop hook updates session count
test_stop_hook() {
    test_start "stop.sh updates session count"

    setup

    "$PLUGIN_ROOT/hooks/stop.sh"

    # Wait for async execution
    sleep 1

    assert_file_exists "$DATA_DIR/session.json"
    assert_file_contains "$DATA_DIR/session.json" "count"

    local count=$(jq -r '.count' "$DATA_DIR/session.json")
    assert_equals "$count" "1"

    test_pass
    teardown
}

# Test: hooks ignore configured tools
test_hook_ignores_tools() {
    test_start "hooks ignore TodoWrite tool"

    setup

    export CLAUDE_TOOL_NAME="TodoWrite"
    export CLAUDE_TOOL_INPUT="test"

    "$PLUGIN_ROOT/hooks/pre-tool.sh"
    sleep 1

    # File should not exist or be empty
    if [ -f "$DATA_DIR/observations.jsonl" ]; then
        local lines=$(wc -l < "$DATA_DIR/observations.jsonl")
        assert_equals "$lines" "0"
    fi

    test_pass
    teardown
}

# Test: hooks never fail (exit 0)
test_hooks_never_fail() {
    test_start "hooks always exit 0"

    setup

    export CLAUDE_TOOL_NAME="Edit"
    export CLAUDE_TOOL_INPUT=""

    "$PLUGIN_ROOT/hooks/pre-tool.sh"
    local pre_exit=$?

    "$PLUGIN_ROOT/hooks/stop.sh"
    local stop_exit=$?

    assert_equals "$pre_exit" "0"
    assert_equals "$stop_exit" "0"

    test_pass
    teardown
}

# Run all tests
echo "Running Hook Tests for instinct-learning"
echo "========================================="
echo ""

test_pre_tool_hook
test_post_tool_hook
test_stop_hook
test_hook_ignores_tools
test_hooks_never_fail

echo ""
echo "========================================="
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
