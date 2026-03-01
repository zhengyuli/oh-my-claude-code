#!/bin/bash
# Instinct-Learning - Observation Hook
#
# Captures tool use events for pattern analysis.
# Claude Code passes hook data via stdin as JSON.
#
# This hook runs asynchronously and does not block tool execution.

set -e

# Support INSTINCT_LEARNING_DATA_DIR environment variable
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
OBS_DIR="${DATA_DIR}/observations"
OBSERVATIONS_FILE="${OBS_DIR}/observations.jsonl"
MAX_FILE_SIZE_MB=2
MAX_ARCHIVE_FILES=10

# Debug logging (optional)
if [ "$DEBUG_HOOKS" = "1" ]; then
  log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] HOOK: $*" >&2
  }
else
  log() { true; }
fi

# Ensure directories exist
mkdir -p "$DATA_DIR"
mkdir -p "$OBS_DIR"

# Skip if disabled
if [ -f "$DATA_DIR/disabled" ]; then
  exit 0
fi

# Read JSON from stdin (Claude Code hook format)
INPUT_JSON=$(cat)

log "Starting hook execution"
log "Observations file: $OBSERVATIONS_FILE"

# Exit if no input
if [ -z "$INPUT_JSON" ]; then
  log "No input received, exiting"
  exit 0
fi

# Acquire lock using mkdir-based atomic locking (portable: macOS + Linux)
# mkdir is atomic - only one process can succeed at creating the directory
LOCK_DIR="${OBS_DIR}/.lockdir"
LOCK_RETRY=0
MAX_LOCK_RETRY=10
LOCK_DELAY=0.01

while [ $LOCK_RETRY -lt $MAX_LOCK_RETRY ]; do
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    # Successfully acquired lock - set up cleanup on exit
    trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT
    log "Lock acquired successfully"
    break
  fi
  # Lock held by another process - wait and retry
  sleep $LOCK_DELAY
  LOCK_RETRY=$((LOCK_RETRY + 1))
done

if [ $LOCK_RETRY -eq $MAX_LOCK_RETRY ]; then
  # Could not acquire lock within timeout - skip this observation
  # Another process is handling observations, which is acceptable
  log "Could not acquire lock after ${MAX_LOCK_RETRY} attempts, skipping"
  exit 0
fi

# ========== Critical Section (protected by mkdir lock) ==========

# Parse using python via stdin pipe (safe for all JSON payloads)
PARSED=$(echo "$INPUT_JSON" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)

    # Extract fields - Claude Code hook format
    hook_type = data.get("hook_type", "unknown")
    tool_name = data.get("tool_name", data.get("tool", "unknown"))
    tool_input = data.get("tool_input", data.get("input", {}))
    tool_output = data.get("tool_output", data.get("output", ""))
    session_id = data.get("session_id", "unknown")

    # Truncate large inputs/outputs to 1000 chars
    if isinstance(tool_input, dict):
        tool_input_str = json.dumps(tool_input)[:1000]
    else:
        tool_input_str = str(tool_input)[:1000]

    if isinstance(tool_output, dict):
        tool_output_str = json.dumps(tool_output)[:1000]
    else:
        tool_output_str = str(tool_output)[:1000]

    # Determine event type
    event = "tool_start" if "Pre" in hook_type else "tool_complete"

    print(json.dumps({
        "parsed": True,
        "event": event,
        "tool": tool_name,
        "input": tool_input_str if event == "tool_start" else None,
        "output": tool_output_str if event == "tool_complete" else None,
        "session": session_id
    }))
except Exception as e:
    print(json.dumps({"parsed": False, "error": str(e)}))
')

# Check if parsing succeeded
PARSED_OK=$(echo "$PARSED" | python3 -c "import json,sys; print(json.load(sys.stdin).get('parsed', False))")

if [ "$PARSED_OK" != "True" ]; then
  exit 0
fi

# Rotate if file too large (numbered archive system)
# Archive naming: observations.1.jsonl, observations.2.jsonl, ..., observations.10.jsonl
# When limit reached: delete .10, rotate .9→.10, .8→.9, ..., current→.1
if [ -f "$OBSERVATIONS_FILE" ]; then
  file_size_mb=$(du -m "$OBSERVATIONS_FILE" 2>/dev/null | cut -f1)
  if [ "${file_size_mb:-0}" -ge "$MAX_FILE_SIZE_MB" ]; then
    # Step 1: Remove oldest archive if at limit (prevents infinite growth)
    if [ -f "${OBS_DIR}/observations.${MAX_ARCHIVE_FILES}.jsonl" ]; then
      rm "${OBS_DIR}/observations.${MAX_ARCHIVE_FILES}.jsonl"
    fi

    # Step 2: Rotate existing archives (highest number first)
    # This order prevents overwriting: .9 → .10 before .8 → .9
    for i in $(seq $((MAX_ARCHIVE_FILES-1)) -1 1); do
      if [ -f "${OBS_DIR}/observations.${i}.jsonl" ]; then
        mv "${OBS_DIR}/observations.${i}.jsonl" "${OBS_DIR}/observations.$((i+1)).jsonl"
      fi
    done

    # Step 3: Move current file to .1 (creates space for new observations)
    mv "$OBSERVATIONS_FILE" "${OBS_DIR}/observations.1.jsonl"
  fi
fi

# Build and write observation (atomic append under lock protection)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

export TIMESTAMP="$timestamp"
echo "$PARSED" | python3 -c "
import json, sys, os

parsed = json.load(sys.stdin)
observation = {
    'timestamp': os.environ['TIMESTAMP'],
    'event': parsed['event'],
    'tool': parsed['tool'],
    'session': parsed['session']
}

if parsed['input']:
    observation['input'] = parsed['input']
if parsed['output']:
    observation['output'] = parsed['output']

print(json.dumps(observation))
" >> "$OBSERVATIONS_FILE"

log "Observation written successfully"

# ========== Critical Section End (trap auto-releases lock on exit) ==========

exit 0
