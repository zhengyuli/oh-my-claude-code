---
name: instinct:analyze
description: Analyze observations to detect patterns and create instincts
---

# Analyze Observations

Manually trigger pattern analysis on captured observations to create or update instincts.

## Usage

```
/instinct:analyze
```

## What It Does

Dispatches the observer agent to analyze observations and create instinct files.

## Prerequisites

- Observations file exists at `~/.claude/instinct-learning/observations.jsonl`
- At least 10 observations captured for meaningful pattern detection

## Implementation

**IMPORTANT: This command ONLY dispatches the observer agent. Do NOT perform analysis yourself.**

Use the Task tool to dispatch the observer agent:

```
Task tool configuration:
- subagent_type: "instinct-learning:observer"
- description: "Analyze observations and create instincts"
```

The observer agent will:
1. Read observations from `~/.claude/instinct-learning/observations.jsonl`
2. Detect patterns (corrections, error resolutions, workflows, preferences)
3. Calculate confidence scores based on frequency
4. Create/update instinct files in `~/.claude/instinct-learning/instincts/personal/`

## Example

```
User: /instinct:analyze

Claude: Dispatching the observer agent to analyze your observations...

[Uses Task tool with subagent_type: "instinct-learning:observer"]

Observer Agent: Analyzing 156 observations...

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
