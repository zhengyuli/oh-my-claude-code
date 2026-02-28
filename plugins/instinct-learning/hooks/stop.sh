#!/bin/bash
# Stop Hook - Session cleanup and statistics tracking
# Part of instinct-learning plugin

set -o pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
SESSION_FILE="$DATA_DIR/session.json"
CONFIG_FILE="$DATA_DIR/config.json"

# Default configuration
MAX_FILE_SIZE_MB=10
ARCHIVE_AFTER_DAYS=7

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    MAX_FILE_SIZE_MB=$(jq -r '.observation.max_file_size_mb // 10' "$CONFIG_FILE" 2>/dev/null || echo "10")
    ARCHIVE_AFTER_DAYS=$(jq -r '.observation.archive_after_days // 7' "$CONFIG_FILE" 2>/dev/null || echo "7")
fi

# Non-blocking execution
{
    # Ensure directory exists
    mkdir -p "$DATA_DIR"

    # Update session statistics
    if [ -f "$SESSION_FILE" ]; then
        session_count=$(jq -r '.count // 0' "$SESSION_FILE" 2>/dev/null || echo "0")
        session_count=$((session_count + 1))
        jq -n \
            --argjson count "$session_count" \
            --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            '{count: $count, last_session: $ts}' > "$SESSION_FILE" 2>/dev/null
    else
        jq -n \
            --argjson count 1 \
            --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            '{count: $count, last_session: $ts}' > "$SESSION_FILE" 2>/dev/null
    fi

    # Check observation file size and archive if necessary
    OBS_FILE="$DATA_DIR/observations.jsonl"
    if [ -f "$OBS_FILE" ]; then
        size=$(wc -c < "$OBS_FILE" 2>/dev/null || echo "0")
        max_size=$((MAX_FILE_SIZE_MB * 1024 * 1024))
        if [ "$size" -gt "$max_size" ]; then
            archive_dir="$DATA_DIR/observations.archive"
            mkdir -p "$archive_dir"
            mv "$OBS_FILE" "$archive_dir/observations-$(date +%Y%m%d-%H%M%S).jsonl" 2>/dev/null
            touch "$OBS_FILE" 2>/dev/null
        fi
    fi

    # Clean up old archives (older than ARCHIVE_AFTER_DAYS)
    if [ -d "$DATA_DIR/observations.archive" ]; then
        find "$DATA_DIR/observations.archive" -name "*.jsonl" -mtime +$ARCHIVE_AFTER_DAYS -delete 2>/dev/null
    fi

} 2>/dev/null &

# Always succeed - never block session end
exit 0
