# Configuration Examples

This document provides ready-to-use configuration samples for various use cases.

## Table of Contents

- [Location](#location)
- [Minimal Configuration](#minimal-configuration)
- [Development Configuration](#development-configuration)
- [Production Configuration](#production-configuration)
- [Testing Configuration](#testing-configuration)
- [Environment-Specific Overrides](#environment-specific-overrides)

---

## Location

Configuration file: `~/.claude/instinct-learning/config.json`

Or set via environment variable:
```bash
export INSTINCT_LEARNING_DATA_DIR=/custom/path
```

---

## Minimal Configuration

Basic settings for getting started with the instinct-learning plugin.

```json
{
  "observation": {
    "capture_tools": [
      "Edit",
      "Write",
      "Bash",
      "Read",
      "Grep"
    ]
  },
  "instincts": {
    "min_confidence": 0.3
  }
}
```

**Use case:** First-time users who want to start observing sessions without advanced customization.

---

## Development Configuration

Debug-enabled configuration for development and testing.

```json
{
  "observation": {
    "capture_tools": [
      "Edit",
      "Write",
      "Bash",
      "Read",
      "Grep",
      "Glob"
    ],
    "ignore_tools": [
      "TodoWrite",
      "TaskCreate"
    ],
    "debug": true
  },
  "instincts": {
    "min_confidence": 0.1,
    "auto_approve_threshold": 0.5
  },
  "evolution": {
    "cluster_threshold": 2,
    "enable_auto_evolution": false
  },
  "pruning": {
    "max_instincts": 50,
    "archive_low_confidence": true
  }
}
```

**Features:**
- Debug mode enabled for verbose logging
- Lower confidence threshold for learning more patterns
- Smaller max instincts limit for faster testing
- Auto-approval threshold set to 50%

**Use case:** Developers working on the plugin or testing new features.

---

## Production Configuration

Optimized configuration for production use.

```json
{
  "observation": {
    "capture_tools": [
      "Edit",
      "Write",
      "Bash",
      "Read",
      "Grep"
    ],
    "ignore_tools": [
      "TodoWrite",
      "TaskCreate",
      "TaskUpdate",
      "AskUserQuestion",
      "Skill"
    ],
    "debug": false
  },
  "instincts": {
    "min_confidence": 0.4,
    "auto_approve_threshold": 0.75
  },
  "evolution": {
    "cluster_threshold": 3,
    "enable_auto_evolution": false
  },
  "pruning": {
    "max_instincts": 100,
    "archive_low_confidence": true
  },
  "decay": {
    "weekly_decay_rate": 0.02,
    "min_confidence_floor": 0.3
  }
}
```

**Features:**
- Higher confidence thresholds for quality instincts
- Larger max instincts limit (100)
- No debug output for better performance
- Auto-approval only for high-confidence instincts (75%+)

**Use case:** Daily development work with mature instinct learning.

---

## Testing Configuration

Configuration optimized for running tests.

```json
{
  "observation": {
    "capture_tools": [
      "Edit",
      "Write"
    ],
    "ignore_tools": [],
    "debug": true
  },
  "instincts": {
    "min_confidence": 0.0,
    "auto_approve_threshold": 0.0
  },
  "evolution": {
    "cluster_threshold": 1,
    "enable_auto_evolution": false
  },
  "pruning": {
    "max_instincts": 10,
    "archive_low_confidence": true
  },
  "test": {
    "mock_data": true,
    "fast_mode": true
  }
}
```

**Features:**
- Zero confidence thresholds for maximum test coverage
- Minimal tool capture for faster tests
- Very small max instincts limit (10)
- Test-specific options

**Use case:** Running the plugin test suite.

---

## Research/Experimentation Configuration

Configuration for exploring patterns and experimenting with the plugin.

```json
{
  "observation": {
    "capture_tools": [
      "Edit",
      "Write",
      "Bash",
      "Read",
      "Grep",
      "Glob",
      "WebFetch",
      "WebSearch"
    ],
    "ignore_tools": [
      "TodoWrite"
    ],
    "debug": true,
    "log_all_events": true
  },
  "instincts": {
    "min_confidence": 0.2,
    "auto_approve_threshold": 0.6
  },
  "evolution": {
    "cluster_threshold": 2,
    "enable_auto_evolution": true,
    "evolution_interval": "daily"
  },
  "pruning": {
    "max_instincts": 200,
    "archive_low_confidence": true
  },
  "decay": {
    "weekly_decay_rate": 0.01,
    "min_confidence_floor": 0.2
  }
}
```

**Features:**
- Captures web-related tools for broader pattern discovery
- Higher max instincts limit (200) for more data
- Lower decay rate for longer retention
- Auto-evolution enabled for continuous improvement

**Use case:** Researchers and users exploring pattern discovery capabilities.

---

## Environment-Specific Overrides

### Per-Project Configuration

Override settings for a specific project:

```bash
export INSTINCT_LEARNING_DATA_DIR=./.instinct-data
```

Then create a project-specific config at `.instinct-data/config.json`:

```json
{
  "instincts": {
    "min_confidence": 0.5,
    "domain": "my-project"
  }
}
```

### CI/CD Configuration

For CI/CD environments with minimal learning:

```json
{
  "observation": {
    "capture_tools": ["Edit", "Write"],
    "debug": false
  },
  "instincts": {
    "min_confidence": 0.8,
    "auto_approve_threshold": 0.9
  },
  "evolution": {
    "enable_auto_evolution": false
  }
}
```

---

## Configuration Reference

### Observation Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `capture_tools` | array | [Edit, Write, Bash, Read, Grep] | Tools to observe |
| `ignore_tools` | array | [TodoWrite, TaskCreate, ...] | Tools to skip |
| `debug` | boolean | false | Enable debug logging |
| `log_all_events` | boolean | false | Log all captured events |

### Instinct Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `min_confidence` | float | 0.3 | Minimum confidence for instincts |
| `auto_approve_threshold` | float | 0.7 | Auto-approve confidence threshold |

### Evolution Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `cluster_threshold` | integer | 3 | Minimum instincts for clustering |
| `enable_auto_evolution` | boolean | false | Enable automatic evolution |
| `evolution_interval` | string | "manual" | Evolution frequency |

### Pruning Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_instincts` | integer | 100 | Maximum instincts to keep |
| `archive_low_confidence` | boolean | true | Archive low-confidence instincts |

### Decay Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `weekly_decay_rate` | float | 0.02 | Confidence decay per week (2%) |
| `min_confidence_floor` | float | 0.3 | Minimum confidence after decay |

---

## Quick Setup Commands

```bash
# Create minimal config
cat > ~/.claude/instinct-learning/config.json << 'EOF'
{
  "observation": {
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep"]
  },
  "instincts": {
    "min_confidence": 0.3
  }
}
EOF

# Create development config
cat > ~/.claude/instinct-learning/config.dev.json << 'EOF'
{
  "observation": {
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "debug": true
  },
  "instincts": {
    "min_confidence": 0.1,
    "auto_approve_threshold": 0.5
  },
  "pruning": {
    "max_instincts": 50
  }
}
EOF

# Use development config
export INSTINCT_LEARNING_CONFIG=~/.claude/instinct-learning/config.dev.json
```
