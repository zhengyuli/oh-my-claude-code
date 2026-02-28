# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**oh-my-claude-code** is a Claude Code plugin marketplace containing multiple plugins for enhanced productivity and workflow automation.

### Marketplace Structure

```
oh-my-claude-code/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace manifest listing all plugins
├── plugins/
│   ├── instinct-learning/  # Plugin: Instinct-based learning system
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json # Plugin manifest
│   │   ├── agents/         # Agent definitions
│   │   ├── commands/       # User commands
│   │   ├── skills/         # Auto-triggered skills
│   │   ├── hooks/          # Hook scripts
│   │   ├── lib/            # Python libraries
│   │   ├── scripts/        # CLI tools
│   │   ├── tests/          # Test suites
│   │   ├── docs/           # Documentation
│   │   ├── config.schema.json # Configuration schema
│   │   └── README.md       # Plugin documentation
│   └── <other-plugins>/    # Additional plugins
├── CLAUDE.md               # This file
└── README.md               # Marketplace overview
```

## Available Plugins

| Plugin | Description |
|--------|-------------|
| **instinct-learning** | Observes sessions, learns patterns, evolves behaviors into skills/commands/agents |

## Testing

### Run All Tests for a Plugin

```bash
# Run all tests for instinct-learning plugin
./plugins/instinct-learning/tests/run-all.sh
```

### Individual Test Suites

```bash
# Hook tests
./plugins/instinct-learning/tests/test-hooks.sh

# Observer agent tests
./plugins/instinct-learning/tests/test-observer.sh

# Session memory tests
./plugins/instinct-learning/tests/test-session-memory.sh

# Integration tests
./plugins/instinct-learning/tests/test-integration.sh

# Python unit tests
python3 ./plugins/instinct-learning/tests/test-pattern-detection.py
python3 ./plugins/instinct-learning/tests/test-instinct-parser.py
python3 ./plugins/instinct-learning/tests/test-clustering.py
python3 ./plugins/instinct-learning/tests/test-confidence.py
```

## Development Commands

### CLI Tool (instinct-learning plugin)

The `instinct-cli.py` script provides advanced management:

```bash
# View all instincts by confidence level
python3 ./plugins/instinct-learning/scripts/instinct-cli.py status

# Filter by domain
python3 ./plugins/instinct-learning/scripts/instinct-cli.py status --domain testing

# Export instincts to file
python3 ./plugins/instinct-learning/scripts/instinct-cli.py export --output instincts.md

# Import instincts from file or URL
python3 ./plugins/instinct-learning/scripts/instinct-cli.py import instincts.md

# Run evolution with dry-run
python3 ./plugins/instinct-learning/scripts/instinct-cli.py evolve --dry-run

# View session statistics
python3 ./plugins/instinct-learning/scripts/instinct-cli.py session --stats
```

### Observer Management (instinct-learning plugin)

```bash
# Start the observer agent
./plugins/instinct-learning/scripts/start-observer.sh

# Stop the observer agent
./plugins/instinct-learning/scripts/stop-observer.sh

# Run observer manually
python3 ./plugins/instinct-learning/scripts/run-observer.py
```

### Environment Initialization (instinct-learning plugin)

```bash
# Initialize the data directory and configuration
./plugins/instinct-learning/scripts/init-env.sh
```

## Adding a New Plugin

1. **Create Plugin Directory**
   ```bash
   mkdir -p plugins/<plugin-name>/.claude-plugin
   ```

2. **Create Plugin Manifest** (`plugins/<plugin-name>/.claude-plugin/plugin.json`)
   ```json
   {
     "name": "plugin-name",
     "version": "1.0.0",
     "description": "Plugin description",
     "author": "author-name",
     "license": "MIT",
     "commands": [],
     "skills": [],
     "agents": [],
     "hooks": {}
   }
   ```

3. **Add Plugin Content** (agents, commands, skills, hooks, etc.)

4. **Update Marketplace** (`.claude-plugin/marketplace.json`)
   ```json
   {
     "plugins": [
       {
         "name": "plugin-name",
         "source": "./plugins/<plugin-name>",
         "description": "Plugin description",
         "version": "1.0.0"
       }
     ]
   }
   ```

5. **Add Plugin Documentation** (`plugins/<plugin-name>/README.md`)

## Plugin Architecture (instinct-learning)

### Data Flow

```
Session Activity → Hooks (PreToolUse/PostToolUse/Stop) → observations.jsonl
                                                            │
                                                            ▼
                                                    Observer Agent (Haiku)
                                                            │
                                                            ▼
                                                    Pattern Detection
                                                            │
                                                            ▼
                                        instincts/personal/ (YAML + Markdown)
                                                            │
                                                            ▼
                                        /instinct:evolve → Clustering → evolved/
                                                                                    │
                                                    ┌─────────────────────────────┴─────────────────────────────┐
                                                    ▼                           ▼                           ▼
                                                skills/                     commands/                    agents/
```

### Key Components

1. **Hooks Layer** (`hooks/*.sh`): Non-blocking observation capture using async background execution
2. **Observer Agent** (`agents/observer.md`): Background agent using Haiku model for cost-efficient pattern detection
3. **Pattern Detection** (`lib/pattern_detection.py`): Detects repeated sequences, error→fix patterns, tool preferences
4. **Confidence Scoring** (`lib/confidence.py`): Scores patterns 0.3-0.9 based on occurrence count and consistency
5. **Clustering** (`lib/clustering.py`): Groups instincts by domain, determines capability type
6. **Evolution Engine**: User-triggered via `/instinct:evolve` command

### Instinct File Format

```markdown
---
id: <unique-kebab-case-id>
trigger: "when <condition>"
confidence: <0.3-0.9>
domain: "<category>"
created: "<ISO-timestamp>"
source: "observation"
evidence_count: <number>
---

# <Short Name>

## Action
<What to do when trigger fires>

## Evidence
- <Observation 1 timestamp>: <Description>
- <Observation 2 timestamp>: <Description>
```

### Domains

- `code-style`: Coding patterns and preferences
- `testing`: Test writing and execution patterns
- `git`: Version control workflows
- `debugging`: Error investigation and fixing
- `workflow`: General development workflow
- `architecture`: System design decisions
- `documentation`: Documentation patterns

## Configuration

### Marketplace Configuration

Located at `.claude-plugin/marketplace.json`:
- Lists all available plugins
- Specifies plugin source directories
- Contains plugin metadata

### Plugin Configuration (instinct-learning)

Location: `~/.claude/instinct-learning/config.json`

Override data directory: `INSTINCT_LEARNING_DATA_DIR`

Key settings:
- `observation.capture_tools`: Tools to observe (default: Edit, Write, Bash, Read, Grep, Glob)
- `observation.ignore_tools`: Tools to skip (default: TodoWrite, TaskCreate, etc.)
- `instincts.min_confidence`: Minimum confidence threshold (default: 0.3)
- `instincts.auto_approve_threshold`: Auto-approval level (default: 0.7)
- `evolution.cluster_threshold`: Minimum instincts for clustering (default: 3)

## Design Principles

1. **Modularity**: Each plugin is self-contained with its own manifest
2. **Non-blocking**: Hooks run asynchronously, never interrupt sessions
3. **Fail-safe**: All components handle errors gracefully
4. **Privacy First**: Observations stored locally, only patterns exportable
5. **Confidence-Based**: Actions weighted by statistical confidence

## Important Notes

- Each plugin directory contains all plugin-specific code
- Plugin manifests are in `.claude-plugin/plugin.json` within each plugin directory
- The root `.claude-plugin/marketplace.json` lists all marketplace plugins
- Library dependencies are minimal (Python standard library + PyYAML)
