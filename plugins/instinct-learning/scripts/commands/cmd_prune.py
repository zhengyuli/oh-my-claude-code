"""
Prune command handler.

This module enforces maximum instincts limit by archiving low-confidence
instincts. It uses effective confidence (after time-based decay) to determine
which instincts to keep, ensuring the most relevant patterns are retained.

Pruning Strategy:
- Calculate effective confidence (base confidence - time decay)
- Sort by effective confidence (highest first)
- Keep top N instincts (default: 100)
- Archive low-confidence instincts to ARCHIVED_DIR

Archived files:
- Moved from personal/inherited to ARCHIVED_DIR
- Name conflicts handled with timestamp suffix
- Can be restored later if needed

Usage:
    # Preview pruning
    $ python3 instinct_cli.py prune --dry-run

    # Force pruning with custom limit
    $ python3 instinct_cli.py prune --max-instincts 50

Constants:
    DEFAULT_MAX_INSTINCTS: 100 (default maximum instincts to keep)
"""

import shutil
from argparse import Namespace
from datetime import datetime
from pathlib import Path

from utils.file_io import load_all_instincts, ARCHIVED_DIR
from utils.confidence import calculate_effective_confidence

# Default settings
DEFAULT_MAX_INSTINCTS = 100


def enforce_max_instincts(max_count: int = DEFAULT_MAX_INSTINCTS, dry_run: bool = False) -> int:
    """Ensure instinct count stays within limit by archiving low-confidence ones.

    The pruning algorithm uses effective confidence (base confidence minus time-based
    decay) to prioritize which instincts to keep. Instincts with the lowest
    effective confidence are archived first.

    Args:
        max_count: Maximum number of instincts to keep
        dry_run: If True, only report what would be archived without actually archiving

    Returns:
        Number of instincts archived (would be archived in dry-run mode)

    Algorithm:
        1. Load all instincts
        2. Calculate effective confidence for each
        3. Sort by effective confidence (descending)
        4. Keep top max_count instincts
        5. Archive the rest

    Example:
        >>> archived = enforce_max_instincts(max_count=50, dry_run=True)
        >>> print(f"Would archive {archived} instincts")
    """
    instincts = load_all_instincts()

    if len(instincts) <= max_count:
        return 0

    # Calculate effective confidence (with decay) for each instinct
    for inst in instincts:
        inst['effective_confidence'] = calculate_effective_confidence(inst)

    # Sort by effective confidence (highest first)
    instincts.sort(key=lambda x: -x.get('effective_confidence', 0.5))

    # Identify instincts to archive (lowest confidence)
    to_archive = instincts[max_count:]

    if dry_run:
        print(f"Would archive {len(to_archive)} instincts (max: {max_count}):")
        for inst in to_archive:
            eff = inst.get('effective_confidence', 0.5)
            print(f"  - {inst.get('id')} (effective confidence: {eff:.2f})")
        return len(to_archive)

    # Archive the low-confidence instincts
    for inst in to_archive:
        src = Path(inst['_source_file'])
        dst = ARCHIVED_DIR / src.name

        # Handle name conflicts by adding timestamp
        if dst.exists():
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            dst = ARCHIVED_DIR / f"{src.stem}-{timestamp}{src.suffix}"

        shutil.move(str(src), str(dst))
        eff = inst.get('effective_confidence', 0.5)
        print(f"Archived: {inst.get('id')} (effective confidence: {eff:.2f})")

    return len(to_archive)


def cmd_prune(args: Namespace) -> int:
    """Enforce max instincts limit by archiving low-confidence ones.

    This is the main entry point for the prune command. It displays current
    statistics, handles dry-run mode, and reports the results of the operation.

    Args:
        args: argparse.Namespace with attributes:
            - max_instincts: Maximum instincts to keep (optional)
            - dry_run: Preview without archiving (optional)

    Returns:
        0 on success.

    Example:
        >>> # In dry-run mode, preview what would be archived
        >>> cmd_prune(Namespace(max_instincts=50, dry_run=True))
    """
    max_instincts = args.max_instincts or DEFAULT_MAX_INSTINCTS

    instincts = load_all_instincts()
    print(f"\nCurrent instincts: {len(instincts)}")
    print(f"Max limit: {max_instincts}")

    if len(instincts) <= max_instincts:
        print("\nNo pruning needed - within limit.")
        return 0

    if args.dry_run:
        print("\n[DRY RUN] Preview of archiving:")
    else:
        num_to_archive = len(instincts) - max_instincts
        print(f"\nArchiving {num_to_archive} lowest-confidence instincts...")

    archived = enforce_max_instincts(max_instincts, dry_run=args.dry_run)

    if not args.dry_run and archived:
        print(f"\nArchived {archived} instincts to {ARCHIVED_DIR}")

    return 0
