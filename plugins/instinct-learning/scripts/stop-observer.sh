#!/bin/bash
# Stop the background observer agent

set -e

# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
PID_FILE="$DATA_DIR/observer.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Observer not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "Observer stopped (PID: $PID)"
else
    rm -f "$PID_FILE"
    echo "Observer was not running (stale PID file removed)"
fi
