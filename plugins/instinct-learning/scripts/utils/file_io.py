"""File I/O operations for instinct management.

Respects INSTINCT_LEARNING_DATA_DIR environment variable for custom data directory.

Directory Structure:
    DATA_DIR/
    ├── instincts/
    │   ├── personal/      # User-created instincts
    │   ├── inherited/     # Imported instincts
    │   └── archived/      # Pruned instincts
    └── observations.jsonl
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from .instinct_parser import parse_instinct_file


# Configuration
_data_dir_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
DATA_DIR = Path(_data_dir_env) if _data_dir_env else Path.home() / ".claude" / "instinct-learning"

INSTINCTS_DIR = DATA_DIR / "instincts"
PERSONAL_DIR = INSTINCTS_DIR / "personal"
INHERITED_DIR = INSTINCTS_DIR / "inherited"
ARCHIVED_DIR = INSTINCTS_DIR / "archived"
OBSERVATIONS_FILE = DATA_DIR / "observations.jsonl"

INSTINCT_FILE_PATTERNS = ['*.yaml', '*.yml', '*.md']
_directories_initialized = False


def _ensure_directories() -> None:
    """Ensure data directories exist (lazy initialization)."""
    global _directories_initialized
    if not _directories_initialized:
        for d in [PERSONAL_DIR, INHERITED_DIR, ARCHIVED_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        _directories_initialized = True


def load_all_instincts() -> List[Dict[str, Any]]:
    """Load all instincts from personal and inherited directories.

    Searches for .md, .yaml, .yml files, sorted alphabetically.
    Adds '_source_file' and '_source_type' metadata to each instinct.

    Returns:
        List of instinct dictionaries with metadata.
    """
    _ensure_directories()
    instincts = []

    for directory in [PERSONAL_DIR, INHERITED_DIR]:
        if not directory.exists():
            continue

        files = sorted(
            set().union(*[set(directory.glob(pattern)) for pattern in INSTINCT_FILE_PATTERNS])
        )

        for file in files:
            try:
                content = file.read_text(encoding='utf-8')
                parsed = parse_instinct_file(content)
                for inst in parsed:
                    inst['_source_file'] = str(file)
                    inst['_source_type'] = directory.name
                instincts.extend(parsed)
            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Failed to parse {file}: {e}", file=sys.stderr)

    return instincts
