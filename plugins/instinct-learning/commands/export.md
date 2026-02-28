---
name: instinct:export
description: Export instincts for sharing
---

# Export Instincts

Export your instincts to a file for sharing or backup.

## Usage

```
/instinct:export [--output <file>] [--domain <domain>] [--min-confidence <0.0-1.0>]
```

## Options

- `--output <file>` - Output file path (default: stdout)
- `--domain <domain>` - Filter by domain (e.g., testing, workflow)
- `--min-confidence <n>` - Minimum confidence threshold

## Example

Export all high-confidence testing instincts:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export --domain testing --min-confidence 0.7 --output testing-instincts.md
```

## Output Format

```markdown
# Instincts export
# Date: 2026-02-28T10:30:00Z
# Total: 5

---
id: test-first-approach
trigger: "when implementing new features"
confidence: 0.9
domain: testing
source: session-observation
---

# Test First Approach

## Action
Always write tests before implementation.
```

## Implementation

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export [options]
```

## Related Commands

- `/instinct:import` - Import instincts
- `/instinct:status` - View all instincts
