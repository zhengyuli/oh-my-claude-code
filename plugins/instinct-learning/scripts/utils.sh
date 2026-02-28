#!/bin/bash
# Common utility functions for instinct-learning scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Data directory
# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"

# Log function
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "${DEBUG:-}" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Ensure data directory exists
ensure_data_dir() {
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/instincts/personal"
    mkdir -p "$DATA_DIR/instincts/shared"
    mkdir -p "$DATA_DIR/evolved/skills"
    mkdir -p "$DATA_DIR/evolved/commands"
    mkdir -p "$DATA_DIR/evolved/agents"
}

# Get config value using jq
get_config() {
    local key="$1"
    local default="${2:-}"
    local config_file="$DATA_DIR/config.json"

    if [ -f "$config_file" ]; then
        local value
        value=$(jq -r "$key // \"$default\"" "$config_file" 2>/dev/null)
        echo "$value"
    else
        echo "$default"
    fi
}

# Check if jq is available
require_jq() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install jq."
        exit 1
    fi
}

# Check if python3 is available
require_python3() {
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed."
        exit 1
    fi
}

# Count observations
count_observations() {
    local obs_file="$DATA_DIR/observations.jsonl"
    if [ -f "$obs_file" ]; then
        wc -l < "$obs_file" | tr -d ' '
    else
        echo "0"
    fi
}

# Count instincts
count_instincts() {
    local count=0
    for dir in personal shared; do
        local instinct_dir="$DATA_DIR/instincts/$dir"
        if [ -d "$instinct_dir" ]; then
            count=$((count + $(find "$instinct_dir" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')))
        fi
    done
    echo "$count"
}

# Get session count
get_session_count() {
    local session_file="$DATA_DIR/session.json"
    if [ -f "$session_file" ]; then
        jq -r '.count // 0' "$session_file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}
