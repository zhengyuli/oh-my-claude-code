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

1. Checks that observations file exists at `~/.claude/instinct-learning/observations.jsonl`
2. Verifies minimum observation count (10+)
3. Dispatches the observer agent to perform AI-based pattern detection
4. Observer creates/updates instincts in `~/.claude/instinct-learning/instincts/personal/`

## Implementation

This command dispatches the observer agent to perform analysis:

```
Use the Task tool to dispatch an observer agent with the following configuration:
- subagent_type: "general-purpose"
- model: "haiku" (for cost-efficiency)
- description: "Analyze observations and create instincts"

The agent should:
1. Read observations from ~/.claude/instinct-learning/observations.jsonl
2. Detect patterns using the criteria defined in agents/observer.md
3. Create or update instinct files in ~/.claude/instinct-learning/instincts/personal/
```

## Observer Agent Instructions

When dispatched, follow the pattern detection rules in `agents/observer.md`:

### Pattern Types to Detect

- **User Corrections**: When user corrects Claude's previous action
- **Error Resolutions**: When an error is followed by a fix
- **Repeated Workflows**: Same tool sequence used multiple times
- **Tool Preferences**: Consistent preference for certain tools

### Confidence Calculation

- 1-2 observations: 0.3 (tentative)
- 3-5 observations: 0.5 (moderate)
- 6-10 observations: 0.7 (strong)
- 11+ observations: 0.85 (very strong)

### Output Format

Create instinct files with this structure:

```markdown
---
id: <kebab-case-id>
trigger: "when <condition>"
confidence: <0.3-0.9>
domain: "<category>"
source: "session-observation"
created: "<ISO-timestamp>"
evidence_count: <number>
---

# <Title>

## Action
<What to do when trigger fires>

## Evidence
- <Observation evidence>
```

## Prerequisites

- At least 10 observations captured
- Observations file exists at `~/.claude/instinct-learning/observations.jsonl`

## Example

```
User: /instinct:analyze

Claude: I'll dispatch the observer agent to analyze your observations.

[Dispatches observer agent using Task tool]

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
