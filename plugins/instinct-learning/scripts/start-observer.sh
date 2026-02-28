#!/bin/bash
# Start the background observer agent
# This launches the observer to analyze observations periodically

set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
PID_FILE="$DATA_DIR/observer.pid"
LOG_FILE="$DATA_DIR/observer.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Observer already running (PID: $OLD_PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

echo "Starting instinct-learning observer..."

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Start observer in background
# The observer runs the pattern detection periodically
(
    while true; do
        # Log timestamp
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Observer cycle started" >> "$LOG_FILE"

        # Check if observations file exists and has content
        OBS_FILE="$DATA_DIR/observations.jsonl"
        if [ -f "$OBS_FILE" ] && [ -s "$OBS_FILE" ]; then
            # Run pattern detection
            python3 "$PLUGIN_ROOT/scripts/run-observer.py" 2>> "$LOG_FILE" || true
        fi

        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Observer cycle completed" >> "$LOG_FILE"

        # Wait for next interval (5 minutes by default)
        sleep 300
    done
) &

OBSERVER_PID=$!
echo $OBSERVER_PID > "$PID_FILE"

echo "Observer started (PID: $OBSERVER_PID)"
echo "Log file: $LOG_FILE"
