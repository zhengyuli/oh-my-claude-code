# API Reference

This document describes the programmatic API for the instinct-learning plugin.

## CLI Tool

The main CLI is located at `scripts/instinct-cli.py`.

### status

Display all learned instincts organized by confidence level.

```bash
python3 scripts/instinct-cli.py status [options]
```

**Options:**
- `--domain, -d <domain>`: Filter by domain
- `--format, -f <json|text>`: Output format (default: text)

**Output:**
- Text: Formatted with confidence groups
- JSON: Structured with high/medium/low arrays

### import

Import instincts from file or URL.

```bash
python3 scripts/instinct-cli.py import <source> [options]
```

**Arguments:**
- `source`: File path or HTTP/HTTPS URL

**Options:**
- `--merge, -m`: Merge with existing instincts

**Behavior:**
- Parses YAML frontmatter + Markdown format
- Saves to `shared/` directory
- Marks source as "imported"

### export

Export instincts to file or stdout.

```bash
python3 scripts/instinct-cli.py export [options]
```

**Options:**
- `--domain, -d <domain>`: Filter by domain
- `--output, -o <file>`: Output file path (default: stdout)

**Output Format:**
YAML frontmatter + Markdown, one instinct after another.

### evolve

Analyze and evolve instincts into capabilities.

```bash
python3 scripts/instinct-cli.py evolve [options]
```

**Options:**
- `--generate, -g`: Generate capability files
- `--dry-run`: Show proposals without generating

**Output:**
Lists clusters with domain, count, confidence, and type.

### session

Manage session information.

```bash
python3 scripts/instinct-cli.py session [options]
```

**Options:**
- `--stats`: Show session statistics

### config

Manage configuration.

```bash
python3 scripts/instinct-cli.py config [options]
```

**Options:**
- `--set <key=value>`: Set a configuration value

**Example:**
```bash
python3 scripts/instinct-cli.py config --set observation.max_prompt_length=1000
```

## Library Modules

### pattern_detection.py

Pattern detection algorithms.

#### `load_observations(file_path: Path) -> list[dict]`

Load observations from JSONL file.

```python
from pattern_detection import load_observations

observations = load_observations(Path('~/.claude/instinct-learning/observations.jsonl'))
```

#### `detect_all_patterns(observations: list[dict]) -> list[Pattern]`

Run all pattern detection algorithms.

```python
from pattern_detection import detect_all_patterns

patterns = detect_all_patterns(observations)
for p in patterns:
    print(f"{p.pattern_type}: {p.pattern} (confidence: {p.confidence})")
```

#### `detect_repeated_sequences(observations, min_occurrences=3) -> list[Pattern]`

Detect repeated tool usage sequences.

#### `detect_error_fix_patterns(observations) -> list[Pattern]`

Detect error followed by fix patterns.

#### `detect_tool_preferences(observations) -> list[Pattern]`

Detect tool usage preferences.

### instinct_parser.py

Parse and generate instinct files.

#### `Instinct` class

Represents a learned instinct.

```python
from instinct_parser import Instinct

instinct = Instinct(
    id='my-instinct',
    trigger='when doing X',
    confidence=0.7,
    domain='testing',
    created='2025-01-15T10:00:00Z',
    action='Do Y instead',
    evidence=['Observed 3 times']
)
```

#### `Instinct.to_markdown() -> str`

Convert instinct to YAML frontmatter + Markdown format.

#### `Instinct.from_markdown(content: str) -> Optional[Instinct]`

Parse instinct from Markdown content.

#### `save_instinct(instinct: Instinct, base_path: Path, category: str) -> Path`

Save instinct to file.

```python
from instinct_parser import save_instinct

file_path = save_instinct(instinct, Path('~/.claude/instinct-learning'), 'personal')
```

#### `load_all_instincts(base_path: Path) -> list[Instinct]`

Load all instincts from personal and shared directories.

### confidence.py

Confidence calculation and management.

#### `calculate_confidence(factors: ConfidenceFactors) -> float`

Calculate final confidence score.

```python
from confidence import calculate_confidence, ConfidenceFactors

factors = ConfidenceFactors(
    occurrence_count=5,
    user_corrections=0,
    consistency_score=0.9
)
confidence = calculate_confidence(factors)  # Returns ~0.7
```

#### `get_confidence_level(confidence: float) -> str`

Get human-readable level: "high", "medium", or "low".

#### `should_auto_apply(confidence: float) -> bool`

Check if instinct should be auto-applied (≥ 0.7).

### clustering.py

Clustering and evolution logic.

#### `Cluster` class

Represents a cluster of related instincts.

```python
from clustering import Cluster

cluster = Cluster(
    domain='testing',
    instincts=[...],
    avg_confidence=0.75,
    capability_type='skill'
)
```

#### `create_clusters(instincts, min_size=3, min_confidence=0.7) -> list[Cluster]`

Create clusters from instincts.

#### `EvolutionEngine` class

Manages the evolution process.

```python
from clustering import EvolutionEngine

engine = EvolutionEngine()
clusters = engine.analyze(instincts)

for cluster in engine.get_ready_clusters():
    suggestion = engine.suggest_evolution(cluster)
    print(f"Suggested: {suggestion['name']}")
```

## Hook Scripts

### Environment Variables

Hooks receive these environment variables:

| Variable | Description |
|----------|-------------|
| `CLAUDE_TOOL_NAME` | Name of the tool being executed |
| `CLAUDE_TOOL_INPUT` | Input to the tool (truncated) |
| `CLAUDE_EXIT_CODE` | Exit code (PostToolUse only) |
| `CLAUDE_SESSION_ID` | Current session identifier |
| `CLAUDE_PLUGIN_ROOT` | Plugin installation directory |
| `INSTINCT_LEARNING_DATA_DIR` | Optional data storage directory override |

### Exit Codes

All hooks exit 0 (success) regardless of internal errors. This ensures:
- Main session is never interrupted
- Errors are logged but don't propagate
- Plugin is always "invisible" to the user

## File Formats

### Observation (JSONL)

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "type": "pre_tool|post_tool",
  "tool": "Edit|Write|Bash|...",
  "exit_code": "0|1",
  "session": "session-id",
  "input": "truncated input...",
  "response": "truncated response..."
}
```

### Instinct (YAML + Markdown)

```markdown
---
id: instinct-id
trigger: "when condition"
confidence: 0.7
domain: "category"
created: "2025-01-15T10:30:00Z"
source: "observation|imported"
evidence_count: 5
---

# Title

## Action
What to do when trigger fires.

## Evidence
- Evidence item 1
- Evidence item 2
```

### Session (JSON)

```json
{
  "count": 42,
  "last_session": "2025-01-15T14:30:00Z"
}
```
