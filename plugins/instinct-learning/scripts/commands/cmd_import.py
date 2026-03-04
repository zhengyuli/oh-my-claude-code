"""Import command handler - imports instincts from files/URLs with duplicate detection."""

import sys
import urllib.request
import urllib.error
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Any

from utils.file_io import load_all_instincts, INHERITED_DIR
from utils.instinct_parser import parse_instinct_file


def _fetch_content(source: str) -> str:
    """Fetch content from URL or file."""
    if source.startswith(('http://', 'https://')):
        with urllib.request.urlopen(source) as response:
            return response.read().decode('utf-8')
    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding='utf-8')


def _categorize_instincts(
    new_instincts: List[Dict[str, Any]],
    existing_instincts: List[Dict[str, Any]]
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Categorize instincts into to_add, to_update, and duplicates."""
    existing_by_id = {i.get('id'): i for i in existing_instincts if i.get('id')}
    to_add, to_update, duplicates = [], [], []

    for inst in new_instincts:
        inst_id = inst.get('id')
        if inst_id in existing_by_id:
            existing = existing_by_id[inst_id]
            if inst.get('confidence', 0) > existing.get('confidence', 0):
                to_update.append(inst)
            else:
                duplicates.append(inst)
        else:
            to_add.append(inst)

    return to_add, to_update, duplicates


def _filter_by_confidence(instincts: List[Dict], min_conf: float) -> List[Dict]:
    """Filter instincts by minimum confidence."""
    return [i for i in instincts if i.get('confidence', 0.5) >= min_conf]


def _print_summary(to_add: List[Dict], to_update: List[Dict], duplicates: List[Dict]) -> None:
    """Print import summary."""
    categories = [
        ("NEW", to_add, "+"),
        ("UPDATE", to_update, "~"),
        ("SKIP (already exists with equal/higher confidence)", duplicates, "-"),
    ]

    for label, items, prefix in categories:
        if items:
            print(f"\n{label} ({len(items)}):")
            for inst in items[:5]:
                conf = inst.get('confidence', 0.5)
                print(f"  {prefix} {inst.get('id')} (confidence: {conf:.2f})")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")


def _write_instinct_file(instinct: Dict, source: str, output_file: Path) -> None:
    """Write a single instinct to its own file."""
    header = f"# Imported from {source}\n# Date: {datetime.now().isoformat()}\n\n"

    frontmatter = (
        f"---\n"
        f"id: {instinct.get('id')}\n"
        f"trigger: \"{instinct.get('trigger', 'unknown')}\"\n"
        f"confidence: {instinct.get('confidence', 0.5)}\n"
        f"domain: {instinct.get('domain', 'general')}\n"
        f"source: inherited\n"
        f"imported_from: \"{source}\"\n"
    )

    if instinct.get('source_repo'):
        frontmatter += f"source_repo: {instinct.get('source_repo')}\n"

    output_file.write_text(
        header + frontmatter + "---\n\n" + instinct.get('content', '') + "\n\n",
        encoding='utf-8'
    )


def cmd_import(args: Namespace) -> int:
    """Import instincts from file or URL.

    Returns 0 on success, 1 on error.
    """
    # Fetch content
    try:
        content = _fetch_content(args.source)
    except (urllib.error.URLError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.source.startswith(('http://', 'https://')):
        print(f"Fetching from URL: {args.source}")

    # Parse instincts
    new_instincts = parse_instinct_file(content)
    if not new_instincts:
        print("No valid instincts found in source.")
        return 1

    print(f"\nFound {len(new_instincts)} instincts to import.\n")

    # Categorize and filter
    to_add, to_update, duplicates = _categorize_instincts(new_instincts, load_all_instincts())
    min_conf = args.min_confidence or 0.0
    to_add = _filter_by_confidence(to_add, min_conf)
    to_update = _filter_by_confidence(to_update, min_conf)

    _print_summary(to_add, to_update, duplicates)

    # Handle early exits
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

    # Write files
    all_to_write = to_add + to_update
    written_files = []

    for inst in all_to_write:
        output_file = INHERITED_DIR / f"{inst.get('id')}.md"
        _write_instinct_file(inst, args.source, output_file)
        written_files.append(output_file)

    print("\n✅ Import complete!")
    print(f"   Added: {len(to_add)}")
    print(f"   Updated: {len(to_update)}")
    print(f"   Files saved:")
    for f in written_files:
        print(f"     - {f}")

    return 0
