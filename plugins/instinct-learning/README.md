# Instinct Learning Plugin

A Claude Code plugin that observes your sessions, learns atomic behaviors with confidence scoring, and evolves them into skills, commands, and agents.

## Features

- **Automatic Observation**: Hooks capture tool usage without interrupting your workflow
- **Pattern Detection**: Identifies repeated sequences, error-fix patterns, and preferences
- **Confidence Scoring**: Behaviors are scored from 0.3 (tentative) to 0.9 (certain)
- **Evolution**: Clusters of instincts evolve into higher-level capabilities
- **Import/Export**: Share learned behaviors with your team
- **Session Memory**: Maintains context across sessions

## Installation

```bash
# Install from marketplace
claude plugin install oh-my-claude-code/instinct-learning
```

## Quick Start

1. **Work Normally** - The hooks automatically capture observations
2. **Check Status** - Run `/instinct:status` to see learned instincts
3. **Evolve** - Run `/instinct:evolve` to generate capabilities from patterns

## Commands

| Command | Description |
|---------|-------------|
| `/instinct:status` | Show all learned instincts with confidence scores |
| `/instinct:evolve` | Cluster instincts and generate capabilities |
| `/instinct:export` | Export instincts for sharing |
| `/instinct:import` | Import instincts from file or URL |
| `/instinct:session` | View session statistics |

## Data Storage

All data is stored locally in `~/.claude/instinct-learning/`:

```
~/.claude/instinct-learning/
├── config.json           # Plugin configuration
├── observations.jsonl    # Current session observations
├── session.json          # Session tracking
├── instincts/
│   ├── personal/         # Auto-learned instincts
│   └── shared/           # Imported instincts
├── evolved/
│   ├── skills/           # Evolved skills
│   ├── commands/         # Evolved commands
│   └── agents/           # Evolved agents
└── observations.archive/ # Archived observations
```

## Architecture

The plugin uses a three-stage pipeline:

1. **Observation** - Non-blocking hooks capture tool usage
2. **Analysis** - Background observer agent detects patterns (uses Haiku for efficiency)
3. **Evolution** - User-triggered clustering generates capabilities

## License

MIT License
