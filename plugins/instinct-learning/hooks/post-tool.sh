#!/bin/bash
# PostToolUse Hook - Enhanced version with error handling and smart truncation
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
MAX_RESPONSE_LENGTH=1000

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    # Use while-read loop instead of mapfile for bash 3.2 compatibility
    if jq -e '.observation.capture_tools' "$CONFIG_FILE" >/dev/null 2>&1; then
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
    MAX_RESPONSE_LENGTH=$(jq -r '.observation.max_response_length // 1000' "$CONFIG_FILE" 2>/dev/null || echo "1000")
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

# Non-blocking execution with comprehensive error handling
{
    # Ensure directory exists
    mkdir -p "$DATA_DIR"

    # Get input from environment or stdin
    tool_input="${CLAUDE_TOOL_INPUT:-}"
    tool_response=$(cat 2>/dev/null || echo "")

    # Truncate long texts
    if [ -n "$tool_input" ]; then
        tool_input=$(truncate_text "$tool_input" "$MAX_PROMPT_LENGTH")
        tool_input=$(echo "$tool_input" | jq -Rs '.' 2>/dev/null || echo '""')
    else
        tool_input='""'
    fi

    if [ -n "$tool_response" ]; then
        tool_response=$(truncate_text "$tool_response" "$MAX_RESPONSE_LENGTH")
        tool_response=$(echo "$tool_response" | jq -Rs '.' 2>/dev/null || echo '""')
    else
        tool_response='""'
    fi

    # Build JSON record using jq for validity
    jq -n \
        --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        --arg type "post_tool" \
        --arg tool "$CLAUDE_TOOL_NAME" \
        --arg exit_code "$CLAUDE_EXIT_CODE" \
        --arg session "$CLAUDE_SESSION_ID" \
        --argjson input "$tool_input" \
        --argjson response "$tool_response" \
        '{timestamp: $ts, type: $type, tool: $tool, exit_code: $exit_code, session: $session, input: $input, response: $response}' \
        >> "$OBSERVATIONS_FILE" 2>/dev/null

} 2>/dev/null &

# Always succeed - never block the main session
exit 0
