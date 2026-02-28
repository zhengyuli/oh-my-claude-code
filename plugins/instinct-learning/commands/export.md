---
name: instinct:export
description: Export instincts for sharing with others
---

# Export Instincts

Export your learned instincts to share with team members or backup.

## Process

1. **Select Instincts**: Choose which instincts to export:
   - All instincts (default)
   - Specific domain only (`--domain testing`)
   - High confidence only

2. **Format Output**: Generate in shareable format:
   - YAML frontmatter + Markdown (default)
   - JSON (for programmatic use)

3. **Output Destination**:
   - File (`--output instincts.md`)
   - stdout (for piping)

## Usage Examples

Export all instincts to file:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py export --output my-instincts.md
```

Export only testing instincts:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py export --domain testing --output testing-patterns.md
```

View in terminal:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py export
```

## Output Format

The exported file contains multiple instincts in YAML frontmatter + Markdown format:

```markdown
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
created: "2025-01-15T10:30:00Z"
source: "observation"
evidence_count: 5
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed in 5 different sessions
- User consistently uses map/filter/reduce

---

---
id: always-test-first
...
```

## Privacy Note

Exported instincts contain:
- ✓ Pattern descriptions (generic)
- ✓ Domain categories
- ✓ Confidence scores
- ✗ No actual code or conversation content
- ✗ No file paths or project-specific details

This makes instincts safe to share without exposing sensitive information.
