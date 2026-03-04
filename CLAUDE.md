# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**oh-my-claude-code** is a Claude Code plugin marketplace containing multiple plugins for enhanced productivity and workflow automation.

### Python Requirements

- **Minimum Python Version**: 3.8 (supports 3.8, 3.9, 3.10, 3.11, 3.12)
- **Dependencies**: pyyaml>=6.0 (see `pyproject.toml`)
- **Dev Dependencies**: pytest, pytest-cov, pytest-mock, mypy, pylint, black, isort

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
│   │   ├── scripts/        # Python libraries and CLI tools
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

### Run All Tests (instinct-learning plugin)

```bash
# Run all tests using shell script
./plugins/instinct-learning/tests/run_all.sh

# Or use pytest directly from plugin directory
cd plugins/instinct-learning && pytest tests/ -v

# With coverage report
./plugins/instinct-learning/tests/run_all.sh --coverage
# or
cd plugins/instinct-learning && pytest --cov=scripts --cov-report=html
```

### Run Tests by Category

```bash
# Unit tests only
cd plugins/instinct-learning && pytest tests/unit/ -v

# Integration tests only
cd plugins/instinct-learning && pytest tests/integration/ -v

# Scenario tests only
cd plugins/instinct-learning && pytest tests/scenarios/ -v

# Using shell script
./plugins/instinct-learning/tests/run_all.sh --unit
./plugins/instinct-learning/tests/run_all.sh --integration
./plugins/instinct-learning/tests/run_all.sh --scenario
```

### Run Individual Test Files or Tests

```bash
# Specific test file
cd plugins/instinct-learning && pytest tests/unit/test_instinct_parser.py -v

# Specific test function
cd plugins/instinct-learning && pytest tests/unit/test_cli_parser.py::TestParseInstinctFile::test_parse_single_instinct -v

# Run tests by marker
cd plugins/instinct-learning && pytest -m unit -v
cd plugins/instinct-learning && pytest -m integration -v
cd plugins/instinct-learning && pytest -m "not slow" -v
```

### Coverage Goals

- **Line Coverage**: 80%+
- **Branch Coverage**: 70%+
- **Function Coverage**: 90%+

View coverage report: `open htmlcov/index.html` (after running with `--cov-report=html`)

## Code Quality

### Type Checking

```bash
cd plugins/instinct-learning && mypy scripts/
```

### Linting

```bash
cd plugins/instinct-learning && pylint scripts/
```

### Code Formatting

```bash
# Check formatting
cd plugins/instinct-learning && black --check scripts/

# Format code
cd plugins/instinct-learning && black scripts/

# Sort imports
cd plugins/instinct-learning && isort scripts/
```

### Style Guidelines

- **Maximum line length**: 100 characters (configured in pyproject.toml)
- **Type hints**: Required for all function signatures
- **Docstrings**: Required for all public functions and classes
- **Functions**: Should be under 50 lines

## Development Commands

### Environment Setup (instinct-learning plugin)

```bash
# Navigate to plugin directory
cd plugins/instinct-learning

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dev dependencies
pip install -e ".[dev]"
```

### CLI Tool (instinct-learning plugin)

The `instinct_cli.py` script provides advanced management:

```bash
# From plugin directory
python3 scripts/instinct_cli.py status
python3 scripts/instinct_cli.py status --domain testing
python3 scripts/instinct_cli.py export --output instincts.md
python3 scripts/instinct_cli.py import instincts.md
python3 scripts/instinct_cli.py evolve --dry-run
```

### User Commands (instinct-learning plugin)

These are slash commands invoked from within Claude Code:

| Command | Description |
|---------|-------------|
| `/instinct:analyze` | Dispatch analyzer agent to analyze observations and create instincts |
| `/instinct:status` | Show all instincts with confidence scores |
| `/instinct:evolve` | Cluster instincts and evolve into skills/commands/agents |
| `/instinct:export` | Export instincts for sharing |
| `/instinct:import` | Import instincts from file or URL |

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
                                                    Analyzer Agent (Haiku)
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
2. **Analyzer Agent** (`agents/analyzer.md`): AI-powered pattern detection using Haiku model for cost efficiency
3. **Evolver Agent** (`agents/evolver.md`): Clusters instincts and evolves them into skills/commands/agents
4. **CLI Tool** (`scripts/instinct_cli.py`): File operations for status/import/export/evolve commands
5. **Pattern Detection** (`scripts/utils/instinct_parser.py`): Parses YAML frontmatter and Markdown content
6. **Confidence Scoring** (`scripts/utils/confidence.py`): Scores patterns 0.3-0.9 based on occurrence count
7. **Evolution Engine**: User-triggered via `/instinct:evolve` command

### Important: Dynamic Skills Generation

The `skills` array in `plugin.json` is intentionally empty. Skills are dynamically generated via the `/instinct:evolve` command and stored in the `evolved/skills/` directory. This allows the system to learn new behaviors over time.

### Security Considerations

- **YAML Injection Prevention**: Instinct parser uses `yaml.safe_load()` to prevent code execution
- **Race Condition Protection**: Atomic file operations prevent data loss during archive cleanup
- **Local-First**: Observations stay on your machine; only patterns can be exported
- **Import Safety**: Review external instincts before importing (see SECURITY-ADVISORY-2026-03-01.md)

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

**Default Data Directory**: `~/.claude/instinct-learning/`

**Override data directory**: Set `INSTINCT_LEARNING_DATA_DIR` environment variable

**Configuration File**: `~/.claude/instinct-learning/config.json`

**Important**: The `instincts/personal/` and `evolved/` directories are located in the user data directory (`~/.claude/instinct-learning/`), not in the plugin directory. The plugin directory contains only code and configuration.

Key settings:
- `observation.enabled`: Enable/disable observation capture (default: true)
- `observation.capture_tools`: Tools to observe (default: Edit, Write, Bash, Read, Grep, Glob)
- `observation.ignore_tools`: Tools to skip (default: TodoWrite, TaskCreate, TaskUpdate, TaskGet, TaskList)
- `instincts.min_confidence`: Minimum confidence threshold (default: 0.3)
- `instincts.auto_approve_threshold`: Auto-approval level (default: 0.7)
- `evolution.cluster_threshold`: Minimum instincts for clustering (default: 3)

## Design Principles

1. **Modularity**: Each plugin is self-contained with its own manifest in `.claude-plugin/plugin.json`
2. **Non-blocking**: Hooks run asynchronously using background execution to never interrupt sessions
3. **Fail-safe**: All components handle errors gracefully with atomic operations for data integrity
4. **Privacy First**: Observations stored locally in `~/.claude/instinct-learning/`, only patterns exportable
5. **Confidence-Based**: Actions weighted by statistical confidence (0.3-0.9) based on observation frequency
6. **AI Agent Model Selection**: Uses Haiku for cost-effective pattern detection; Sonnet/Opus for complex tasks

## Important Notes

- Each plugin directory contains all plugin-specific code
- Plugin manifests are in `.claude-plugin/plugin.json` within each plugin directory
- The root `.claude-plugin/marketplace.json` lists all marketplace plugins
- Python dependencies are minimal (pyyaml>=6.0) - see `pyproject.toml`
- Confidence scores range from 0.3 (tentative) to 0.9 (near-certain)
- Skills are dynamically generated via `/instinct:evolve` - not listed in plugin.json
- For detailed testing documentation, see `plugins/instinct-learning/tests/README.md`
