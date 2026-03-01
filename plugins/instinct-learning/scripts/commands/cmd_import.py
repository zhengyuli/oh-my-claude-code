"""
Import command handler.

This module handles importing instincts from external sources (files or URLs)
into the instinct-learning system. It provides duplicate detection,
confidence-based filtering, and user confirmation workflows.

Features:
- Import from local files or remote URLs
- Duplicate detection and handling (update if higher confidence, skip otherwise)
- Confidence-based filtering
- Dry-run mode for preview
- User confirmation prompts (can be bypassed with --force)
- One file per instinct (uses instinct ID as filename)

Import Workflow:
1. Fetch content from source (file or URL)
2. Parse YAML frontmatter instincts
3. Categorize into: new, updates, duplicates
4. Apply confidence filtering
5. Show preview and get confirmation
6. Write each instinct to a separate file in inherited directory

Output Format:
    Imported instincts are saved to INHERITED_DIR with:
    - One file per instinct (named {id}.md)
    - Source attribution (imported_from field)
    - Import date in file header
    - YAML frontmatter with all metadata
    - Original markdown content

Example:
    $ python3 instinct_cli.py import instincts.md --dry-run
    $ python3 instinct_cli.py import https://example.com/instincts.md --force
"""

import sys
import urllib.request
import urllib.error
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Any

from utils.file_io import load_all_instincts, INHERITED_DIR
from utils.instinct_parser import parse_instinct_file


def _fetch_content_from_url(source: str) -> str:
    """Fetch content from URL.

    Args:
        source: URL to fetch from

    Returns:
        Content as string

    Raises:
        urllib.error.URLError: If URL fetch fails
    """
    with urllib.request.urlopen(source) as response:
        return response.read().decode('utf-8')


def _fetch_content_from_file(source: str) -> str:
    """Fetch content from file path.

    Args:
        source: File path

    Returns:
        Content as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding='utf-8')


def _categorize_instincts(
    new_instincts: List[Dict[str, Any]],
    existing_instincts: List[Dict[str, Any]]
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Categorize instincts into to_add, to_update, and duplicates.

    Args:
        new_instincts: List of new instincts to import
        existing_instincts: List of existing instincts

    Returns:
        Tuple of (to_add, to_update, duplicates) lists
    """
    existing_ids = {i.get('id') for i in existing_instincts}
    existing_by_id = {i.get('id'): i for i in existing_instincts if i.get('id')}

    to_add = []
    duplicates = []
    to_update = []

    for inst in new_instincts:
        inst_id = inst.get('id')
        if inst_id in existing_ids:
            existing_inst = existing_by_id.get(inst_id)
            if existing_inst:
                if inst.get('confidence', 0) > existing_inst.get('confidence', 0):
                    to_update.append(inst)
                else:
                    duplicates.append(inst)
        else:
            to_add.append(inst)

    return to_add, to_update, duplicates


def _filter_by_confidence(
    instincts: List[Dict],
    min_confidence: float
) -> List[Dict]:
    """Filter instincts by minimum confidence.

    Args:
        instincts: List of instincts
        min_confidence: Minimum confidence threshold

    Returns:
        Filtered list of instincts
    """
    return [i for i in instincts if i.get('confidence', 0.5) >= min_confidence]


def _print_import_summary(
    to_add: List[Dict],
    to_update: List[Dict],
    duplicates: List[Dict]
) -> None:
    """Print summary of import operations.

    Args:
        to_add: List of instincts to add
        to_update: List of instincts to update
        duplicates: List of duplicate instincts
    """
    if to_add:
        print(f"NEW ({len(to_add)}):")
        for inst in to_add:
            print(f"  + {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if to_update:
        print(f"\nUPDATE ({len(to_update)}):")
        for inst in to_update:
            print(f"  ~ {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if duplicates:
        print(f"\nSKIP ({len(duplicates)} - already exists with equal/higher confidence):")
        for inst in duplicates[:5]:
            print(f"  - {inst.get('id')}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")


def _write_single_instinct_file(
    instinct: Dict,
    source: str,
    output_file: Path
) -> None:
    """Write a single instinct to its own file.

    Args:
        instinct: Single instinct dictionary to write
        source: Original source identifier
        output_file: Output file path
    """
    iso_date = datetime.now().isoformat()
    output_content = (
        f"# Imported from {source}\n"
        f"# Date: {iso_date}\n\n"
        f"---\n"
        f"id: {instinct.get('id')}\n"
        f"trigger: \"{instinct.get('trigger', 'unknown')}\"\n"
        f"confidence: {instinct.get('confidence', 0.5)}\n"
        f"domain: {instinct.get('domain', 'general')}\n"
        f"source: inherited\n"
        f"imported_from: \"{source}\"\n"
    )

    if instinct.get('source_repo'):
        output_content += f"source_repo: {instinct.get('source_repo')}\n"

    output_content += f"---\n\n"
    output_content += instinct.get('content', '') + "\n\n"

    output_file.write_text(output_content, encoding='utf-8')


def _fetch_import_content(source: str) -> str:
    """Fetch content from URL or file for import.

    Args:
        source: File path or URL

    Returns:
        Content as string

    Raises:
        urllib.error.URLError: If URL fetch fails
        FileNotFoundError: If file doesn't exist
    """
    if source.startswith(('http://', 'https://')):
        return _fetch_content_from_url(source)
    return _fetch_content_from_file(source)


def cmd_import(args: Namespace) -> int:
    """Import instincts from file or URL.

    Args:
        args: argparse.Namespace with attributes:
            - source: File path or URL to import from
            - dry_run: Preview without importing (optional)
            - force: Skip confirmation (optional)
            - min_confidence: Minimum confidence threshold (optional)

    Returns:
        0 on success, 1 on error.
    """
    # Fetch content
    try:
        content = _fetch_import_content(args.source)
    except (urllib.error.URLError, FileNotFoundError) as e:
        print(f"Error: {getattr(e, 'str', str(e))}", file=sys.stderr)
        return 1

    # Print URL fetch message
    if args.source.startswith(('http://', 'https://')):
        print(f"Fetching from URL: {args.source}")

    # Parse instincts
    new_instincts = parse_instinct_file(content)
    if not new_instincts:
        print("No valid instincts found in source.")
        return 1

    print(f"\nFound {len(new_instincts)} instincts to import.\n")

    # Categorize instincts
    to_add, to_update, duplicates = _categorize_instincts(
        new_instincts,
        load_all_instincts()
    )

    # Filter by confidence
    min_conf = args.min_confidence or 0.0
    to_add = _filter_by_confidence(to_add, min_conf)
    to_update = _filter_by_confidence(to_update, min_conf)

    # Print summary
    _print_import_summary(to_add, to_update, duplicates)

    # Handle early exits (dry run, nothing to import, cancelled)
    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return 0

    if not to_add and not to_update:
        print("\nNothing to import.")
        return 0

    if not args.force:
        if input(f"\nImport {len(to_add)} new, update {len(to_update)}? [y/N] ").lower() != 'y':
            print("Cancelled.")
            return 0

    # Write output files (one file per instinct)
    all_to_write = to_add + to_update
    written_files = []

    for inst in all_to_write:
        output_file = INHERITED_DIR / f"{inst.get('id')}.md"
        _write_single_instinct_file(inst, args.source, output_file)
        written_files.append(output_file)

    print("\n✅ Import complete!")
    print(f"   Added: {len(to_add)}")
    print(f"   Updated: {len(to_update)}")
    print(f"   Files saved:")
    for f in written_files:
        print(f"     - {f}")

    return 0
