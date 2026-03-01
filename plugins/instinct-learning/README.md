# Instinct-Learning Plugin

An instinct-based learning system that observes your Claude Code sessions, learns atomic behaviors with confidence scoring, and evolves them into skills/commands/agents.

## Features

- **Hook-based Observation**: Captures 100% of tool use events via PreToolUse/PostToolUse hooks
- **AI-powered Analysis**: `/instinct:analyze` dispatches analyzer agent (Haiku) for pattern detection
- **Confidence Scoring**: Each instinct has a confidence score (0.3-0.9) based on observation frequency
- **Import/Export**: Share instincts with your team

## Installation

Install from the oh-my-claude-code marketplace.

## Commands

| Command | Description |
|---------|-------------|
| `/instinct:analyze` | Dispatch analyzer agent to analyze observations and create instincts |
| `/instinct:status` | Show all instincts with confidence scores |
| `/instinct:export [options]` | Export instincts for sharing |
| `/instinct:import <source>` | Import instincts from file or URL |

## Data Directory

```
~/.claude/instinct-learning/
├── config.json           # User configuration
├── observations.jsonl    # Observation data (captured by hooks)
├── instincts/
│   ├── personal/         # AI-learned instincts (from /instinct:analyze)
│   └── inherited/        # Imported instincts
└── evolved/
    ├── agents/           # Evolved agents (via /instinct:evolve command)
    ├── skills/           # Evolved skills (via /instinct:evolve command)
    └── commands/         # Evolved commands (via /instinct:evolve command)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA FLOW                                    │
└─────────────────────────────────────────────────────────────────┘

Session Activity
      │
      │ hooks/observe.sh captures (100% reliable)
      ▼
observations.jsonl
      │
      │ /instinct:analyze (manual trigger)
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Analyzer Agent (Haiku)                        │
│  - Reads observations.jsonl                                      │
│  - Detects patterns (corrections, workflows, preferences)        │
│  - Creates/updates instinct files                                │
└─────────────────────────────────────────────────────────────────┘
      │
      │ Creates
      ▼
instincts/personal/*.md
      │
      │ /instinct:evolve (clustering)
      ▼
evolved/
├── skills/
├── commands/
└── agents/
```

## Components

| Component | Type | Responsibility |
|-----------|------|----------------|
| `hooks/observe.sh` | Script | Capture tool use events |
| `hooks/hooks.json` | Config | Hook configuration |
| `agents/analyzer.md` | Agent | AI-powered pattern detection |
| `commands/analyze.md` | Command | Dispatch analyzer agent |
| `commands/status.md` | Command | Show instinct status |
| `commands/evolve.md` | Command | Cluster instincts |
| `commands/export.md` | Command | Export instincts |
| `commands/import.md` | Command | Import instincts |
| `scripts/instinct_cli.py` | CLI | File operations for status/import/export/evolve |

## Instinct File Format

```markdown
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.75
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
2. **Analyze**: Run `/instinct:analyze` to dispatch analyzer agent
3. **Learn**: Analyzer creates instincts with confidence scores

## Privacy & Security

- Observations stay local on your machine
- Only instincts (patterns) can be exported
- No actual code or conversation content is shared
- **Security:** Instinct parser uses `yaml.safe_load()` to prevent code injection
- **Security:** Race condition protection prevents data loss during archive cleanup

**Important:** If you import instincts from external sources, review the [Security Advisory](docs/SECURITY-ADVISORY-2026-03-01.md) for best practices.

See [docs/SECURITY-ADVISORY-2026-03-01.md](docs/SECURITY-ADVISORY-2026-03-01.md) for details on recent security improvements.

## Testing

```bash
# Run all tests
./tests/run_all.sh

# Run specific test suites
python3 tests/test_instinct_cli.py -v
python3 tests/test_hooks.py -v
python3 tests/test_integration.py -v
```

## Running Tests

See [tests/README.md](tests/README.md) for detailed testing guide.

Quick start:
```bash
./tests/run_all.sh              # All tests
./tests/run_all.sh --coverage   # With coverage report
```
