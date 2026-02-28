# Instinct-Learning Plugin Refactor Design

## Overview

Refactor the instinct-learning plugin based on v2 code (`plugins/continuous-learning-v2/`), converting from a skill to a proper Claude Code plugin with manual analysis triggering.

## Key Changes from v2

| Aspect | v2 | New Design |
|--------|-----|------------|
| Type | Skill | Plugin |
| Data Directory | `~/.claude/homunculus/` | `~/.claude/instinct-learning/` |
| Observer Trigger | Background daemon (every 5 min) | Manual `/instinct:analyze` command |
| Config Management | Single config.json | Schema + user config separation |
| File Naming | Mixed (hyphens/underscores) | Python style (underscores) |
| Parser Logic | Embedded in CLI | Merged into CLI |

## Plugin Structure

```
plugins/instinct-learning/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── analyze.md               # /instinct:analyze - trigger pattern analysis
│   ├── status.md                # /instinct:status - show instinct status
│   ├── evolve.md                # /instinct:evolve - evolve into skills/commands
│   ├── export.md                # /instinct:export - export instincts
│   └── import.md                # /instinct:import - import instincts
├── agents/
│   └── observer.md              # Observer agent definition
├── hooks/
│   ├── hooks.json               # Hook configuration
│   └── observe.sh               # Observation hook script
├── scripts/
│   └── instinct_cli.py          # CLI tool (includes parsing logic)
├── config.schema.json           # Configuration schema
└── README.md
```

## Data Directory Structure

```
~/.claude/instinct-learning/
├── config.json                  # User configuration
├── observations.jsonl           # Observation data
├── observations.archive/        # Archived observations
├── instincts/
│   ├── personal/                # Auto-learned instincts
│   └── inherited/               # Imported instincts
└── evolved/
    ├── agents/                  # Evolved agents
    ├── skills/                  # Evolved skills
    └── commands/                # Evolved commands
```

## Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Instinct Learning Configuration",
  "type": "object",
  "properties": {
    "observation": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "max_file_size_mb": { "type": "integer", "default": 10 },
        "archive_after_days": { "type": "integer", "default": 7 },
        "capture_tools": {
          "type": "array",
          "default": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"]
        },
        "ignore_tools": {
          "type": "array",
          "default": ["TodoWrite", "TaskCreate", "TaskUpdate"]
        }
      }
    },
    "instincts": {
      "type": "object",
      "properties": {
        "min_confidence": { "type": "number", "default": 0.3 },
        "auto_approve_threshold": { "type": "number", "default": 0.7 },
        "confidence_decay_rate": { "type": "number", "default": 0.02 },
        "max_instincts": { "type": "integer", "default": 100 }
      }
    },
    "evolution": {
      "type": "object",
      "properties": {
        "cluster_threshold": { "type": "integer", "default": 3 },
        "auto_evolve": { "type": "boolean", "default": false }
      }
    }
  }
}
```

## Core Components

| Component | Responsibility | Trigger |
|-----------|---------------|---------|
| observe.sh | Capture tool call events | Hook (PreToolUse/PostToolUse) |
| observer.md | Analyze observations, create instincts | `/instinct:analyze` command |
| instinct_cli.py | CLI tool for status/import/export/evolve | Command invocation |

## Data Flow

```
Session Activity
      │
      │ hooks/observe.sh captures (100% reliable)
      ▼
+-------------------------------------+
|    ~/.claude/instinct-learning/     |
|    observations.jsonl               |
+-------------------------------------+
      │
      │ /instinct:analyze manual trigger
      ▼
+-------------------------------------+
|         Observer Agent              |
|   - Detect user correction patterns |
|   - Detect error resolution patterns|
|   - Detect repeated workflows       |
+-------------------------------------+
      │
      │ Creates/updates
      ▼
+-------------------------------------+
|    instincts/personal/              |
|    - prefer_grep_before_edit.md     |
|    - test_first_approach.md         |
+-------------------------------------+
      │
      │ /instinct:evolve clustering
      ▼
+-------------------------------------+
|         evolved/                    |
|   - skills/testing_workflow.md      |
|   - commands/new_feature.md         |
+-------------------------------------+
```

## Commands

| Command | Description |
|---------|-------------|
| `/instinct:analyze` | Analyze observations and create/update instincts |
| `/instinct:status` | Show all instincts with confidence scores |
| `/instinct:evolve` | Cluster instincts into skills/commands/agents |
| `/instinct:export` | Export instincts for sharing |
| `/instinct:import <file>` | Import instincts from others |

## Instinct File Format

```markdown
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.65
domain: "workflow"
source: "session-observation"
created: "2026-02-28T10:30:00Z"
evidence_count: 8
---

# Prefer Grep Before Edit

## Action
Always use Grep to find the exact location before using Edit.

## Evidence
- Observed 8 times in session abc123
- Pattern: Grep → Read → Edit sequence
- Last observed: 2026-02-28
```

## Domains

- `code-style`: Coding patterns and preferences
- `testing`: Test writing and execution patterns
- `git`: Version control workflows
- `debugging`: Error investigation and fixing
- `workflow`: General development workflow
- `architecture`: System design decisions
- `documentation`: Documentation patterns

## Confidence Scoring

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggested but not enforced |
| 0.5 | Moderate | Applied when relevant |
| 0.7 | Strong | Auto-approved for application |
| 0.9 | Near-certain | Core behavior |

**Confidence increases** when:
- Pattern is repeatedly observed
- User doesn't correct the suggested behavior

**Confidence decreases** when:
- User explicitly corrects the behavior
- Pattern isn't observed for extended periods

## Design Decisions

1. **Manual Analysis**: Removed background daemon in favor of explicit `/instinct:analyze` command for user control
2. **Plugin over Skill**: Using proper plugin structure with commands, agents, and hooks
3. **Unified Config**: Schema-based configuration with user overrides
4. **Python Naming**: Consistent underscore naming for Python files
5. **Merged Parser**: Parsing logic consolidated into `instinct_cli.py` for simplicity
