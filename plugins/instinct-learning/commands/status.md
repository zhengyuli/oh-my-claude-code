---
name: instinct:status
description: Show all learned instincts with confidence scores
---

# Show Instinct Status

Display all learned instincts organized by confidence level, with statistics and evolution readiness.

## Process

1. Load all instincts from `~/.claude/instinct-learning/instincts/` (both personal and shared)
2. Group by confidence level:
   - **High (0.7+)**: Auto-approved, applied automatically
   - **Medium (0.5-0.7)**: Applied when relevant
   - **Low (0.3-0.5)**: Tentative, need more evidence
3. Show statistics and evolution opportunities

## Output Format

```
### High Confidence (0.7+) - Auto-Approved
- [0.9] always-test-first: when implementing new features
- [0.8] prefer-functional: when writing new functions

### Medium Confidence (0.5-0.7) - Applied When Relevant
- [0.6] use-zod-validation: when validating API inputs
- [0.5] commit-often: when making progress

### Low Confidence (0.3-0.5) - Tentative
- [0.4] prefer-async: when writing I/O operations

## Stats
Total: 5 | High: 2 | Medium: 2 | Low: 1
Sessions: 12

Evolution ready: testing (3 instincts, avg 0.75)
```

## Actions

Execute the status command by running the CLI tool:

```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py status
```

If no instincts exist, suggest:
- Continue working normally to generate observations
- Observations are captured automatically via hooks
- Instincts are created after 3+ occurrences of a pattern
