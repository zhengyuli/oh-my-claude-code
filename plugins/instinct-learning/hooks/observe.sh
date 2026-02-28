#!/bin/bash
# Instinct-Learning - Observation Hook
#
# Captures tool use events for pattern analysis.
# Claude Code passes hook data via stdin as JSON.
#
# This hook runs asynchronously and does not block tool execution.

set -e

DATA_DIR="${HOME}/.claude/instinct-learning"
OBSERVATIONS_FILE="${DATA_DIR}/observations.jsonl"
MAX_FILE_SIZE_MB=10

# Ensure directory exists
mkdir -p "$DATA_DIR"

# Skip if disabled
if [ -f "$DATA_DIR/disabled" ]; then
  exit 0
fi

# Read JSON from stdin (Claude Code hook format)
INPUT_JSON=$(cat)

# Exit if no input
if [ -z "$INPUT_JSON" ]; then
  exit 0
fi

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

# Archive if file too large
if [ -f "$OBSERVATIONS_FILE" ]; then
  file_size_mb=$(du -m "$OBSERVATIONS_FILE" 2>/dev/null | cut -f1)
  if [ "${file_size_mb:-0}" -ge "$MAX_FILE_SIZE_MB" ]; then
    archive_dir="${DATA_DIR}/observations.archive"
    mkdir -p "$archive_dir"
    mv "$OBSERVATIONS_FILE" "$archive_dir/observations-$(date +%Y%m%d-%H%M%S).jsonl"
  fi
fi

# Build and write observation
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

exit 0
