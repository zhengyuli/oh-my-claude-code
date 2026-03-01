---
name: instinct:analyze
description: Analyze observations to detect patterns and create instincts
keywords: ["analyze", "observations", "patterns", "instincts", "learning"]
---

# Analyze Observations

Manually trigger pattern analysis on captured observations to create or update instincts.

## Usage

```
/instinct:analyze
```

## What It Does

Dispatches the analyzer agent to analyze observations and create instinct files.

## Prerequisites

- Archived observation files exist at `~/.claude/instinct-learning/observations/observations.*.jsonl`
  - Active observations are written to `observations.jsonl` and archived when complete
- At least 10 observations recommended for meaningful pattern detection (patterns form with 3+)

## Pre-flight Checks

Before dispatching the analyzer agent, verify:

```bash
# 1. Check observations directory exists
OBS_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}/observations"
if [ ! -d "$OBS_DIR" ]; then
  echo "❌ Observations directory not found: $OBS_DIR"
  echo "   Run some commands first to capture observations."
  exit 1
fi

# 2. Check for archived observation files
ARCHIVE_COUNT=$(ls "$OBS_DIR"/observations.*.jsonl 2>/dev/null | wc -l | tr -d ' ')
if [ "$ARCHIVE_COUNT" -eq 0 ]; then
  echo "⚠️  No archived observations found."
  echo "   Current file may still be active. Try again later."
  echo "   Minimum 10 observations recommended for meaningful analysis."
  exit 1
fi

# 3. Count total observations
TOTAL_OBS=$(cat "$OBS_DIR"/observations.*.jsonl 2>/dev/null | wc -l | tr -d ' ')
if [ "$TOTAL_OBS" -lt 10 ]; then
  echo "⚠️  Only $TOTAL_OBS observations found (recommended: 10+)"
  echo "   Pattern detection requires 3+ observations per pattern."
  echo "   Continue anyway? (y/N)"
  read -r response
  if [ "$response" != "y" ]; then
    exit 0
  fi
fi

echo "✅ Pre-flight checks passed: $TOTAL_OBS observations ready for analysis"
```

**Error Messages**:
- ❌ Directory not found
- ⚠️  No archived files (file may be active)
- ⚠️  Limited observations (recommended 10+, patterns form with 3+)

## Implementation

**IMPORTANT: This command ONLY dispatches the analyzer agent. Do NOT perform analysis yourself.**

Use the Task tool to dispatch the analyzer agent:

```
Task tool configuration:
- subagent_type: "instinct-learning:analyzer"
- description: "Analyze observations and create instincts"
```

The analyzer agent will:
1. Read observations from `~/.claude/instinct-learning/observations/observations.*.jsonl` (archived files only)
2. Detect patterns (corrections, error resolutions, workflows, preferences)
3. Calculate confidence scores based on frequency
4. Create/update instinct files in `~/.claude/instinct-learning/instincts/personal/`

## Example

```
User: /instinct:analyze

Claude: Dispatching the analyzer agent to analyze your observations...

[Uses Task tool with subagent_type: "instinct-learning:analyzer"]

Analyzer Agent: Analyzing 156 observations...

Detected patterns:
1. Tool sequence: Grep → Read → Edit (8 occurrences)
2. Testing pattern: pytest before commit (5 occurrences)

Created instincts:
- prefer-grep-before-edit (confidence: 0.75)
- test-before-commit (confidence: 0.70)
```

## Related Commands

- `/instinct:status` - View all learned instincts
- `/instinct:evolve` - Cluster instincts into capabilities
