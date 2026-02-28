---
name: status
description: Show all learned instincts with confidence scores
---

# Instinct Status

Display all learned instincts grouped by domain with confidence scores.

## Usage

```
/status
```

## What It Shows

- Total number of instincts
- Breakdown by source (personal vs inherited)
- Instincts grouped by domain
- Confidence scores with visual bars

## Output Format

```
============================================================
  INSTINCT STATUS - 12 total
============================================================

  Personal:  8
  Inherited: 4

## WORKFLOW (5)

  ███████░░░  70%  prefer-grep-before-edit
            trigger: when searching for code to modify

## TESTING (3)

  █████████░  90%  test-first-approach
            trigger: when implementing new features

─────────────────────────────────────────────────────────
  Observations: 156 events logged
```

## Implementation

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py status
```

## Related Commands

- `/analyze` - Trigger pattern analysis
- `/export` - Export instincts for sharing
