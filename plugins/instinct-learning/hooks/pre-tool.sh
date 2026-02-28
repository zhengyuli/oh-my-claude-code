#!/bin/bash
# PreToolUse Hook - Non-blocking, records tool call start
# Part of instinct-learning plugin

set -o pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
OBSERVATIONS_FILE="$DATA_DIR/observations.jsonl"
CONFIG_FILE="$DATA_DIR/config.json"

# Default configuration
CAPTURE_TOOLS=("Edit" "Write" "Bash" "Read" "Grep" "Glob")
IGNORE_TOOLS=("TodoWrite" "TaskCreate" "TaskUpdate" "TaskList" "AskUserQuestion")
MAX_PROMPT_LENGTH=500

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    # Parse capture_tools from config (simplified, bash 3.2 compatible)
    if jq -e '.observation.capture_tools' "$CONFIG_FILE" >/dev/null 2>&1; then
        # Use while-read loop instead of mapfile for bash 3.2 compatibility
        CAPTURE_TOOLS=()
        while IFS= read -r tool; do
            [ -n "$tool" ] && CAPTURE_TOOLS+=("$tool")
        done < <(jq -r '.observation.capture_tools[]' "$CONFIG_FILE" 2>/dev/null)
    fi
    if jq -e '.observation.ignore_tools' "$CONFIG_FILE" >/dev/null 2>&1; then
        IGNORE_TOOLS=()
        while IFS= read -r tool; do
            [ -n "$tool" ] && IGNORE_TOOLS+=("$tool")
        done < <(jq -r '.observation.ignore_tools[]' "$CONFIG_FILE" 2>/dev/null)
    fi
    MAX_PROMPT_LENGTH=$(jq -r '.observation.max_prompt_length // 500' "$CONFIG_FILE" 2>/dev/null || echo "500")
fi

# Check if tool is in ignore list
for ignore in "${IGNORE_TOOLS[@]}"; do
    if [ "$CLAUDE_TOOL_NAME" = "$ignore" ]; then
        exit 0  # Silently ignore
    fi
done

# Check if tool should be captured
should_capture=false
for tool in "${CAPTURE_TOOLS[@]}"; do
    if [ "$CLAUDE_TOOL_NAME" = "$tool" ]; then
        should_capture=true
        break
    fi
done

if [ "$should_capture" = false ]; then
    exit 0
fi

# Smart truncation function
truncate_text() {
    local text="$1"
    local max_len="$2"
    local len=${#text}
    if [ "$len" -gt "$max_len" ]; then
        echo "${text:0:$max_len}... [truncated, $len chars total]"
    else
        echo "$text"
    fi
}

# Non-blocking execution - record tool call start
{
    # Ensure directory exists
    mkdir -p "$DATA_DIR"

    # Get tool input from environment
    tool_input="${CLAUDE_TOOL_INPUT:-}"

    # Truncate long text
    if [ -n "$tool_input" ]; then
        tool_input=$(truncate_text "$tool_input" "$MAX_PROMPT_LENGTH")
        # Escape for JSON
        tool_input=$(echo "$tool_input" | jq -Rs '.' 2>/dev/null || echo '""')
    else
        tool_input='""'
    fi

    # Build JSON record using jq for validity
    jq -n \
        --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        --arg type "pre_tool" \
        --arg tool "$CLAUDE_TOOL_NAME" \
        --arg session "$CLAUDE_SESSION_ID" \
        --argjson input "$tool_input" \
        '{timestamp: $ts, type: $type, tool: $tool, session: $session, input: $input}' \
        >> "$OBSERVATIONS_FILE" 2>/dev/null

} 2>/dev/null &

# Always succeed - never block the main session
exit 0
