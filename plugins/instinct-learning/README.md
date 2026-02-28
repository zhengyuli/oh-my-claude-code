# Instinct-Learning Plugin

An instinct-based learning system that observes your Claude Code sessions, learns atomic behaviors with confidence scoring, and evolves them into skills/commands/agents.

## Features

- **Hook-based Observation**: Captures 100% of tool use events via PreToolUse/PostToolUse hooks
- **Manual Analysis**: Trigger pattern analysis on-demand with `/instinct:analyze`
- **Confidence Scoring**: Each instinct has a confidence score (0.3-0.9) based on observation frequency
- **Evolution**: Cluster related instincts into skills, commands, or agents
- **Import/Export**: Share instincts with your team

## Installation

Install from the oh-my-claude-code marketplace.

## Commands

| Command | Description |
|---------|-------------|
| `/instinct:analyze` | Analyze observations and create/update instincts |
| `/instinct:status` | Show all instincts with confidence scores |
| `/instinct:evolve` | Cluster instincts into skills/commands/agents |
| `/instinct:export` | Export instincts for sharing |
| `/instinct:import <file>` | Import instincts from others |

## Data Directory

```
~/.claude/instinct-learning/
├── config.json           # User configuration
├── observations.jsonl    # Observation data
├── instincts/
│   ├── personal/         # Auto-learned instincts
│   └── inherited/        # Imported instincts
└── evolved/
    ├── agents/           # Evolved agents
    ├── skills/           # Evolved skills
    └── commands/         # Evolved commands
```

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
```

## Configuration

Edit `~/.claude/instinct-learning/config.json` to customize:

```json
{
  "observation": {
    "enabled": true,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate"]
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7
  },
  "evolution": {
    "cluster_threshold": 3
  }
}
```

## How It Works

1. **Capture**: Hooks automatically capture tool use events
2. **Analyze**: Run `/instinct:analyze` to detect patterns
3. **Learn**: Instincts are created with confidence scores
4. **Evolve**: Run `/instinct:evolve` to cluster into capabilities

## Privacy

- Observations stay local on your machine
- Only instincts (patterns) can be exported
- No actual code or conversation content is shared
