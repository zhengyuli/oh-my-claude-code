"""
File I/O operations for instinct management.

This module provides functions for loading instincts from directories
and managing instinct file storage. It respects the INSTINCT_LEARNING_DATA_DIR
environment variable for custom data directory locations.

Directory Structure:
    DATA_DIR/
    ├── instincts/
    │   ├── personal/      # User-created instincts
    │   ├── inherited/     # Imported instincts from other sources
    │   └── archived/      # Old instincts that were pruned
    └── observations.jsonl    # Raw observation data

Environment Variables:
    INSTINCT_LEARNING_DATA_DIR: Override default data directory location

Example:
    >>> export INSTINCT_LEARNING_DATA_DIR=/custom/path
    >>> load_all_instincts()  # Will use /custom/path/instincts
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

from .instinct_parser import parse_instinct_file


# Configuration - respect INSTINCT_LEARNING_DATA_DIR environment variable
_data_dir_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
if _data_dir_env:
    DATA_DIR = Path(_data_dir_env)
else:
    DATA_DIR = Path.home() / ".claude" / "instinct-learning"

INSTINCTS_DIR = DATA_DIR / "instincts"
PERSONAL_DIR = INSTINCTS_DIR / "personal"
INHERITED_DIR = INSTINCTS_DIR / "inherited"
ARCHIVED_DIR = INSTINCTS_DIR / "archived"
OBSERVATIONS_FILE = DATA_DIR / "observations.jsonl"

# Ensure directories exist
for d in [PERSONAL_DIR, INHERITED_DIR, ARCHIVED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_all_instincts() -> List[Dict[str, Any]]:
    """Load all instincts from personal and inherited directories.

    This function searches for instinct files (.md, .yaml, .yml) in both
    the personal and inherited instinct directories. Each loaded instinct is
    annotated with '_source_file' and '_source_type' metadata for tracking.

    File Processing:
    - Files are sorted alphabetically for consistent ordering
    - Parsing errors are logged but don't stop the loading process
    - Multiple instincts per file are supported

    Metadata Added:
        - '_source_file': Full path to the source file
        '_source_type': Either 'personal' or 'inherited'

    Returns:
        List of instinct dictionaries. Empty list if directories don't exist
        or no instinct files are found.

    Example:
        >>> instincts = load_all_instincts()
        >>> len(instincts) > 0
        True
        >>> instincts[0]['_source_file']
        '/path/to/instinct.yaml'
        >>> instincts[0]['_source_type']
        'personal'
    """
    instincts = []

    for directory in [PERSONAL_DIR, INHERITED_DIR]:
        if not directory.exists():
            continue
        # Collect all instinct files (sorted alphabetically)
        yaml_files = sorted(
            set(directory.glob("*.yaml"))
            | set(directory.glob("*.yml"))
            | set(directory.glob("*.md"))
        )
        for file in yaml_files:
            try:
                content = file.read_text(encoding='utf-8')
                parsed = parse_instinct_file(content)
                # Add metadata to each instinct
                for inst in parsed:
                    inst['_source_file'] = str(file)
                    inst['_source_type'] = directory.name
                instincts.extend(parsed)
            except (OSError, UnicodeDecodeError) as e:
                # Log error but continue processing other files
                print(f"Warning: Failed to parse {file}: {e}", file=sys.stderr)

    return instincts
