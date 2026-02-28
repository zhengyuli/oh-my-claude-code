# Data Formats

This document describes the data formats used by the instinct-learning plugin.

## Observation Format (JSONL)

Observations are stored in JSONL format (JSON Lines), where each line is a valid JSON object.

### PreToolUse Observation

Recorded before a tool executes:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "type": "pre_tool",
  "tool": "Edit",
  "session": "abc123-def456",
  "input": "Edit file src/main.ts to add..."
}
```

### PostToolUse Observation

Recorded after a tool completes:

```json
{
  "timestamp": "2025-01-15T10:30:05Z",
  "type": "post_tool",
  "tool": "Edit",
  "exit_code": "0",
  "session": "abc123-def456",
  "input": "Edit file src/main.ts...",
  "response": "Successfully edited..."
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 UTC timestamp |
| `type` | string | `pre_tool` or `post_tool` |
| `tool` | string | Tool name (Edit, Write, Bash, etc.) |
| `exit_code` | string | Exit code (`0` = success, `1` = failure) |
| `session` | string | Unique session identifier |
| `input` | string | Tool input (truncated to max_prompt_length) |
| `response` | string | Tool response (truncated to max_response_length) |

### Truncation

Long inputs and responses are truncated:

```
"input": "This is a very long input that gets truncated... [truncated, 5000 chars total]"
```

## Instinct Format (YAML Frontmatter + Markdown)

Instincts are stored as Markdown files with YAML frontmatter.

### Structure

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
Use functional patterns over classes when appropriate:
- Pure functions without side effects
- Immutability with spread operators
- Higher-order functions for transformations

## Evidence
- 2025-01-10: Observed in session abc123
- 2025-01-12: Observed in session def456
- 2025-01-14: Observed in session ghi789
- 2025-01-15: Reconfirmed with consistent usage
- 2025-01-15: No corrections detected
```

### YAML Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (kebab-case) |
| `trigger` | string | Yes | When this instinct should fire |
| `confidence` | float | Yes | Score from 0.3 to 0.9 |
| `domain` | string | Yes | Category (code-style, testing, etc.) |
| `created` | string | Yes | ISO 8601 creation timestamp |
| `source` | string | Yes | `observation` or `imported` |
| `evidence_count` | integer | Yes | Number of supporting observations |

### Markdown Body

The body consists of two sections:

1. **Action**: What to do when the trigger fires
2. **Evidence**: List of supporting observations

### Domains

Standard domain categories:

| Domain | Description |
|--------|-------------|
| `code-style` | Coding patterns and preferences |
| `testing` | Test writing and execution patterns |
| `git` | Version control workflows |
| `debugging` | Error investigation and fixing |
| `workflow` | General development workflow |
| `architecture` | System design decisions |
| `documentation` | Documentation patterns |

## Configuration Format (JSON)

Configuration is stored in JSON format:

```json
{
  "version": "1.0",
  "observation": {
    "enabled": true,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate", "TaskList"],
    "max_prompt_length": 500,
    "max_response_length": 1000,
    "max_file_size_mb": 10,
    "archive_after_days": 7
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts_per_domain": 20
  },
  "observer": {
    "enabled": true,
    "model": "haiku",
    "run_interval_minutes": 5,
    "patterns_to_detect": [
      "repeated_sequences",
      "error_fix",
      "user_preferences",
      "domain_patterns"
    ]
  },
  "evolution": {
    "cluster_threshold": 3,
    "min_avg_confidence": 0.7
  },
  "session": {
    "track_sessions": true,
    "memory_enabled": true
  }
}
```

## Session Format (JSON)

Session tracking data:

```json
{
  "count": 42,
  "last_session": "2025-01-15T14:30:00Z"
}
```

## Export Format (YAML + Markdown)

Exported instincts use the same format as individual instincts, concatenated:

```markdown
---
id: instinct-1
trigger: "when X"
confidence: 0.7
...
---

# Instinct 1

...

---
id: instinct-2
trigger: "when Y"
confidence: 0.6
...
---

# Instinct 2

...
```

Multiple instincts are separated by blank lines. Each has its own YAML frontmatter.

## Confidence Levels

| Score | Level | Meaning |
|-------|-------|---------|
| 0.9 | Near-certain | Core behavior, always applied |
| 0.7-0.8 | Strong | Auto-approved for application |
| 0.5-0.7 | Moderate | Applied when relevant |
| 0.3-0.5 | Tentative | Suggested but not enforced |

## File Naming

### Instincts

Pattern: `{id}.md`

Examples:
- `prefer-functional-style.md`
- `always-test-first.md`
- `commit-often-202501151030.md`

### Archived Observations

Pattern: `observations-{timestamp}.jsonl`

Examples:
- `observations-20250115-143000.jsonl`

### Evolved Capabilities

Pattern: `{name}.md`

Examples:
- `testing-workflow.md` (skill)
- `git-task.md` (command)
- `debugging-specialist.md` (agent)
