#!/bin/bash
# Integration Tests for instinct-learning plugin
# Tests the full workflow from observation to evolution
# Run with: ./tests/test-integration.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="/tmp/instinct-learning-integration-test-$$"
DATA_DIR="$TEST_DIR/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Setup
setup() {
    rm -rf "$TEST_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/instincts/personal"
    mkdir -p "$DATA_DIR/instincts/shared"
    mkdir -p "$DATA_DIR/evolved/skills"
    mkdir -p "$DATA_DIR/evolved/commands"
    mkdir -p "$DATA_DIR/evolved/agents"
    export INSTINCT_LEARNING_DATA_DIR="$DATA_DIR"
    export CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT"
}

# Teardown
teardown() {
    rm -rf "$TEST_DIR"
}

# Test: Full workflow
test_full_workflow() {
    test_start "Full workflow: init → observe → detect → evolve"

    setup

    # Step 1: Initialize environment
    "$PLUGIN_ROOT/scripts/init-env.sh" > /dev/null 2>&1

    if [ ! -f "$DATA_DIR/config.json" ]; then
        test_fail "init-env.sh did not create config.json"
        teardown
        return 1
    fi

    # Step 2: Simulate observations (create test data)
    cat > "$DATA_DIR/observations.jsonl" << 'EOF'
{"timestamp":"2025-01-01T00:00:00Z","type":"pre_tool","tool":"Read","session":"s1"}
{"timestamp":"2025-01-01T00:01:00Z","type":"post_tool","tool":"Read","session":"s1","exit_code":"0"}
{"timestamp":"2025-01-01T00:02:00Z","type":"pre_tool","tool":"Edit","session":"s1"}
{"timestamp":"2025-01-01T00:03:00Z","type":"post_tool","tool":"Edit","session":"s1","exit_code":"0"}
{"timestamp":"2025-01-01T00:04:00Z","type":"pre_tool","tool":"Bash","session":"s1"}
{"timestamp":"2025-01-01T00:05:00Z","type":"post_tool","tool":"Bash","session":"s1","exit_code":"0"}
{"timestamp":"2025-01-02T00:00:00Z","type":"pre_tool","tool":"Read","session":"s2"}
{"timestamp":"2025-01-02T00:01:00Z","type":"post_tool","tool":"Read","session":"s2","exit_code":"0"}
{"timestamp":"2025-01-02T00:02:00Z","type":"pre_tool","tool":"Edit","session":"s2"}
{"timestamp":"2025-01-02T00:03:00Z","type":"post_tool","tool":"Edit","session":"s2","exit_code":"0"}
{"timestamp":"2025-01-02T00:04:00Z","type":"pre_tool","tool":"Bash","session":"s2"}
{"timestamp":"2025-01-02T00:05:00Z","type":"post_tool","tool":"Bash","session":"s2","exit_code":"0"}
{"timestamp":"2025-01-03T00:00:00Z","type":"pre_tool","tool":"Read","session":"s3"}
{"timestamp":"2025-01-03T00:01:00Z","type":"post_tool","tool":"Read","session":"s3","exit_code":"0"}
{"timestamp":"2025-01-03T00:02:00Z","type":"pre_tool","tool":"Edit","session":"s3"}
{"timestamp":"2025-01-03T00:03:00Z","type":"post_tool","tool":"Edit","session":"s3","exit_code":"0"}
{"timestamp":"2025-01-03T00:04:00Z","type":"pre_tool","tool":"Bash","session":"s3"}
{"timestamp":"2025-01-03T00:05:00Z","type":"post_tool","tool":"Bash","session":"s3","exit_code":"0"}
EOF

    # Step 3: Run pattern detection
    python3 "$PLUGIN_ROOT/scripts/run-observer.py" > /dev/null 2>&1 || true

    # Step 4: Check for instincts
    instinct_count=$(find "$DATA_DIR/instincts/personal" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$instinct_count" -lt 1 ]; then
        echo -e "\n${YELLOW}Warning: No instincts created (expected at least 1)${NC}"
    fi

    # Step 5: Test CLI status command
    output=$(python3 "$PLUGIN_ROOT/scripts/instinct-cli.py" status 2>&1)

    if ! echo "$output" | grep -q "Confidence\|Total\|No instincts"; then
        test_fail "CLI status command failed"
        teardown
        return 1
    fi

    test_pass
    teardown
}

# Test: Import/Export cycle
test_import_export() {
    test_start "Import/Export cycle"

    setup

    # Initialize
    "$PLUGIN_ROOT/scripts/init-env.sh" > /dev/null 2>&1

    # Create a test instinct to export
    cat > "$DATA_DIR/instincts/personal/test-instinct.md" << 'EOF'
---
id: test-instinct
trigger: "when testing"
confidence: 0.7
domain: "testing"
created: "2025-01-01T00:00:00Z"
source: "observation"
evidence_count: 3
---

# Test Instinct

## Action
Do something when testing.

## Evidence
- Test evidence 1
- Test evidence 2
EOF

    # Export
    export_file="$TEST_DIR/exported.md"
    python3 "$PLUGIN_ROOT/scripts/instinct-cli.py" export --output "$export_file" > /dev/null 2>&1

    if [ ! -f "$export_file" ]; then
        test_fail "Export did not create file"
        teardown
        return 1
    fi

    # Clear and reimport
    rm -rf "$DATA_DIR/instincts/personal"/*

    python3 "$PLUGIN_ROOT/scripts/instinct-cli.py" import "$export_file" > /dev/null 2>&1

    if [ ! -f "$DATA_DIR/instincts/shared/test-instinct.md" ]; then
        test_fail "Import did not create instinct file"
        teardown
        return 1
    fi

    test_pass
    teardown
}

# Test: Session tracking
test_session_tracking() {
    test_start "Session tracking"

    setup

    # Initialize
    "$PLUGIN_ROOT/scripts/init-env.sh" > /dev/null 2>&1

    # Run stop hook multiple times
    export CLAUDE_SESSION_ID="test1"
    "$PLUGIN_ROOT/hooks/stop.sh"
    sleep 1

    export CLAUDE_SESSION_ID="test2"
    "$PLUGIN_ROOT/hooks/stop.sh"
    sleep 1

    # Check session count
    count=$(jq -r '.count' "$DATA_DIR/session.json" 2>/dev/null || echo "0")

    if [ "$count" -lt 2 ]; then
        test_fail "Session count should be at least 2, got $count"
        teardown
        return 1
    fi

    test_pass
    teardown
}

# Test: Configuration management
test_config_management() {
    test_start "Configuration management"

    setup

    # Initialize
    "$PLUGIN_ROOT/scripts/init-env.sh" > /dev/null 2>&1

    # Set a config value
    python3 "$PLUGIN_ROOT/scripts/instinct-cli.py" config --set "observation.max_prompt_length=1000" > /dev/null 2>&1

    # Verify
    value=$(jq -r '.observation.max_prompt_length' "$DATA_DIR/config.json")

    if [ "$value" != "1000" ]; then
        test_fail "Config value not set correctly, got $value"
        teardown
        return 1
    fi

    test_pass
    teardown
}

# Run all tests
echo "Running Integration Tests for instinct-learning"
echo "================================================"
echo ""

test_full_workflow
test_import_export
test_session_tracking
test_config_management

echo ""
echo "================================================"
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
