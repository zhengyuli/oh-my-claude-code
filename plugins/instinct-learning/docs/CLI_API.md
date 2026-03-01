# CLI API Reference

This document provides a comprehensive reference for the Instinct-Learning Plugin CLI and its internal APIs.

## Table of Contents

- [Overview](#overview)
- [CLI Commands](#cli-commands)
- [Module API](#module-api)
- [Utility Functions](#utility-functions)
- [Data Structures](#data-structures)

---

## Overview

The Instinct-Learning Plugin CLI is organized into modular components:

```
scripts/
├── instinct_cli.py          # Main entry point
├── cli_parser.py            # Argument parsing
├── commands/                # Command handlers
│   ├── cmd_status.py
│   ├── cmd_export.py
│   ├── cmd_import.py
│   ├── cmd_prune.py
│   └── cmd_decay.py
└── utils/                   # Utility modules
    ├── file_io.py
    ├── confidence.py
    └── instinct_parser.py
```

---

## CLI Commands

### status

Display all learned instincts with confidence scores.

```bash
python3 instinct_cli.py status [--domain DOMAIN] [--min-confidence MIN]
```

**Options:**
- `--domain DOMAIN`: Filter by domain
- `--min-confidence MIN`: Minimum confidence threshold

**Returns:** 0 on success

### export

Export instincts to a file.

```bash
python3 instinct_cli.py export [--output FILE] [--domain DOMAIN] [--min-confidence MIN]
```

**Options:**
- `--output FILE, -o FILE`: Output file path
- `--domain DOMAIN`: Filter by domain
- `--min-confidence MIN`: Minimum confidence threshold

**Returns:** 0 on success, 1 if no instincts match

### import

Import instincts from a file or URL.

```bash
python3 instinct_cli.py import SOURCE [--dry-run] [--force] [--min-confidence MIN]
```

**Arguments:**
- `SOURCE`: File path or URL

**Options:**
- `--dry-run`: Preview without importing
- `--force`: Skip confirmation
- `--min-confidence MIN`: Minimum confidence threshold

**Returns:** 0 on success, 1 on error

### prune

Enforce max instincts limit by archiving low-confidence ones.

```bash
python3 instinct_cli.py prune [--max-instincts N] [--dry-run]
```

**Options:**
- `--max-instincts N`: Maximum instincts to keep (default: 100)
- `--dry-run`: Preview without archiving

**Returns:** 0 on success

### decay

Show effective confidence after time-based decay.

```bash
python3 instinct_cli.py decay [--decay-rate RATE]
```

**Options:**
- `--decay-rate RATE`: Weekly decay rate (default: 0.02)

**Returns:** 0 on success

---

## Module API

### cli_parser.py

Argument parsing module.

```python
def create_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser.

    Returns:
        Configured ArgumentParser instance with all subcommands.
    """

def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv)

    Returns:
        Parsed arguments as Namespace object.
    """
```

### commands/cmd_status.py

Status display command.

```python
def cmd_status(args: argparse.Namespace) -> int:
    """Show status of all instincts with confidence scores.

    Args:
        args: Namespace with optional attributes:
            - domain: Filter by domain (optional)
            - min_confidence: Minimum confidence threshold (optional)

    Returns:
        0 on success.
    """
```

### commands/cmd_export.py

Export command.

```python
def cmd_export(args: argparse.Namespace) -> int:
    """Export instincts to file.

    Args:
        args: Namespace with attributes:
            - output: Output file path (optional)
            - domain: Filter by domain (optional)
            - min_confidence: Minimum confidence threshold (optional)

    Returns:
        0 on success, 1 if no instincts match.
    """
```

### commands/cmd_import.py

Import command.

```python
def cmd_import(args: argparse.Namespace) -> int:
    """Import instincts from file or URL.

    Args:
        args: Namespace with attributes:
            - source: File path or URL
            - dry_run: Preview without importing
            - force: Skip confirmation
            - min_confidence: Minimum confidence threshold

    Returns:
        0 on success, 1 on error.
    """
```

### commands/cmd_prune.py

Prune command.

```python
def enforce_max_instincts(max_count: int = 100, dry_run: bool = False) -> int:
    """Ensure instinct count stays within limit by archiving low-confidence ones.

    Args:
        max_count: Maximum number of instincts to keep
        dry_run: If True, only report what would be archived

    Returns:
        Number of instincts archived
    """

def cmd_prune(args: argparse.Namespace) -> int:
    """Enforce max instincts limit by archiving low-confidence ones.

    Args:
        args: Namespace with attributes:
            - max_instincts: Maximum instincts to keep
            - dry_run: Preview without archiving

    Returns:
        0 on success.
    """
```

### commands/cmd_decay.py

Decay command.

```python
def cmd_decay(args: argparse.Namespace) -> int:
    """Show effective confidence after decay for all instincts.

    Args:
        args: Namespace with attributes:
            - decay_rate: Weekly decay rate

    Returns:
        0 on success.
    """
```

---

## Utility Functions

### utils/confidence.py

Confidence calculation with time-based decay.

```python
# Constants
DEFAULT_DECAY_RATE = 0.02  # Weekly decay rate (2%)
MIN_CONFIDENCE = 0.3       # Floor for decayed confidence

def calculate_effective_confidence(
    instinct: dict,
    decay_rate: float = DEFAULT_DECAY_RATE
) -> float:
    """Calculate confidence with time-based decay.

    Args:
        instinct: Instinct dict with confidence and last_observed fields
        decay_rate: Weekly decay rate (default 0.02)

    Returns:
        Effective confidence after decay (floored at MIN_CONFIDENCE)
    """
```

### utils/instinct_parser.py

YAML frontmatter parser.

```python
def parse_instinct_file(content: str) -> List[Dict[str, Any]]:
    """Parse instinct file in YAML frontmatter + markdown format.

    Args:
        content: Raw file content as string

    Returns:
        List of instinct dictionaries with parsed frontmatter fields.
        Only instincts with valid 'id' field are included.
    """
```

### utils/file_io.py

File I/O operations.

```python
# Directory paths (respect INSTINCT_LEARNING_DATA_DIR env var)
DATA_DIR = Path.home() / ".claude" / "instinct-learning"
INSTINCTS_DIR = DATA_DIR / "instincts"
PERSONAL_DIR = INSTINCTS_DIR / "personal"
INHERITED_DIR = INSTINCTS_DIR / "inherited"
ARCHIVED_DIR = INSTINCTS_DIR / "archived"
OBSERVATIONS_FILE = DATA_DIR / "observations.jsonl"

def load_all_instincts() -> List[Dict[str, Any]]:
    """Load all instincts from personal and inherited directories.

    Returns:
        List of instinct dictionaries. Empty list if no files found.
        Each instinct has '_source_file' and '_source_type' metadata.
    """
```

---

## Data Structures

### Instinct Dictionary

```python
{
    'id': str,                    # Unique identifier (kebab-case)
    'trigger': str,               # When the instinct applies
    'confidence': float,          # Base confidence (0.3-1.0)
    'domain': str,                # Category (testing, workflow, etc.)
    'source': str,                # Origin of instinct
    'last_observed': str,         # ISO timestamp of last observation
    'created': str,               # ISO timestamp of creation
    'content': str,               # Markdown content
    '_source_file': str,          # File path (metadata)
    '_source_type': str,          # 'personal' or 'inherited' (metadata)
}
```

### CLI Arguments Namespace

Each command receives an `argparse.Namespace` object with relevant attributes.

**Example for export command:**
```python
{
    'output': '/path/to/file.md',
    'domain': 'testing',
    'min_confidence': 0.7
}
```

---

## Environment Variables

### INSTINCT_LEARNING_DATA_DIR

Override the default data directory location.

```bash
export INSTINCT_LEARNING_DATA_DIR=/custom/path
```

**Default:** `~/.claude/instinct-learning`

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (no instincts found, file not found, etc.) |

---

## Usage Examples

```python
# Parse arguments
from cli_parser import parse_args

args = parse_args(['status', '--domain', 'testing'])

# Load instincts
from utils import load_all_instincts

instincts = load_all_instincts()

# Calculate confidence
from utils import calculate_effective_confidence

effective = calculate_effective_confidence(instinct)

# Parse instinct file
from utils import parse_instinct_file

instincts = parse_instinct_file(file_content)
```
