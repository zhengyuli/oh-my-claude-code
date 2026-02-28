---
name: analyze
description: Analyze observations to detect patterns and create instincts
---

# Analyze Observations

Manually trigger pattern analysis on captured observations to create or update instincts.

## Usage

```
/instinct:analyze
```

## What It Does

1. Reads observations from `~/.claude/instinct-learning/observations.jsonl`
2. Uses the observer agent (Haiku) to detect patterns
3. Creates or updates instincts in `~/.claude/instinct-learning/instincts/personal/`

## Pattern Types Detected

- **User Corrections**: When you correct Claude's previous action
- **Error Resolutions**: When an error is followed by a fix
- **Repeated Workflows**: Same sequence of tools used multiple times
- **Tool Preferences**: Consistent preference for certain tools

## Prerequisites

- At least 10 observations captured
- Observations file exists at `~/.claude/instinct-learning/observations.jsonl`

## Example

After several coding sessions, run:

```
/instinct:analyze
```

The agent will analyze your observations and create instincts.

## Related Commands

- `/instinct:status` - View all learned instincts
- `/instinct:evolve` - Cluster instincts into capabilities
