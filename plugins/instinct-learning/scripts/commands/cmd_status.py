"""
Status command handler.

This module displays comprehensive information about learned instincts,
including confidence scores, domain groupings, and system statistics. The
output is formatted for easy reading with confidence bars and grouping.

Display Format:
- Header with total instinct count
- Personal vs inherited breakdown
- Domain-grouped instinct listings
- Confidence bars (█/░) for visual confidence representation
- Action snippets extracted from content
- Observation file statistics

Confidence Bar:
- 10 characters total (█ for filled, ░ for empty)
- Shows percentage: ████████░░ 85%
- Each █ represents 10% confidence

Usage:
    # Show all instincts
    $ python3 instinct_cli.py status

    # Show only testing instincts
    $ python3 instinct_cli.py status --domain testing

Output Interpretation:
- Personal: User-created instincts in this environment
- Inherited: Imported instincts from external sources
- Domains: Categorized automatically (testing, workflow, etc.)
- Confidence bars: Visual representation of confidence level
"""

import re
from collections import defaultdict
from argparse import Namespace

from utils.file_io import (
    load_all_instincts,
    PERSONAL_DIR,
    INHERITED_DIR,
    OBSERVATIONS_FILE,
)


def cmd_status(args: Namespace) -> int:
    """Display all learned instincts with confidence scores.

    This function loads all instincts from both personal and inherited
    directories, groups them by domain, and displays them in a formatted
    output with confidence bars, trigger descriptions, and action snippets.

    Args:
        args: argparse.Namespace (reserved for future filtering options)
            Currently unused but reserved for future domain filtering

    Returns:
        0 on success (always succeeds, displays message if no instincts)

    Output Format:
        - Total instinct count with personal/inherited breakdown
        - Domain-grouped sections with instinct listings
        - Confidence bars (10 characters: █ for filled, ░ for empty)
        - Trigger descriptions and action snippets
        - Observation file statistics if available
    """
    _ = args  # Reserved for future filtering options

    instincts = load_all_instincts()

    if not instincts:
        print("No instincts found.")
        print("\nInstinct directories:")
        print(f"  Personal:  {PERSONAL_DIR}")
        print(f"  Inherited: {INHERITED_DIR}")
        return 0

    # Group instincts by domain
    by_domain = defaultdict(list)
    for inst in instincts:
        by_domain[inst.get('domain', 'general')].append(inst)

    # Count personal vs inherited
    personal_count = sum(1 for i in instincts if i.get('_source_type') == 'personal')
    inherited_count = len(instincts) - personal_count

    # Print header
    print(f"\n{'='*60}")
    print(f"  INSTINCT STATUS - {len(instincts)} total")
    print(f"{'='*60}\n")
    print(f"  Personal:  {personal_count}")
    print(f"  Inherited: {inherited_count}")
    print()

    # Print each domain
    for domain in sorted(by_domain.keys()):
        print(f"## {domain.upper()} ({len(by_domain[domain])})")
        print()

        for inst in sorted(by_domain[domain], key=lambda x: -x.get('confidence', 0.5)):
            conf = inst.get('confidence', 0.5)
            conf_bar = '█' * int(conf * 10) + '░' * (10 - int(conf * 10))
            print(f"  {conf_bar} {int(conf*100):3d}%  {inst.get('id', 'unnamed')}")
            print(f"            trigger: {inst.get('trigger', 'unknown trigger')}")

            action_match = re.search(
                r'## Action\s*\n\s*(.+?)(?:\n\n|\n##|$)',
                inst.get('content', ''),
                re.DOTALL
            )
            if action_match:
                action = action_match.group(1).strip().split('\n')[0]
                print(f"            action: {action[:60] + '...' if len(action) > 60 else action}")
            print()

    # Print observations info
    if OBSERVATIONS_FILE.exists():
        with open(OBSERVATIONS_FILE, encoding='utf-8') as f:
            obs_count = sum(1 for _ in f)
        print("─────────────────────────────────────────────────")
        print(f"  Observations: {obs_count} events logged")
        print(f"  File: {OBSERVATIONS_FILE}")
    print(f"\n{'='*60}\n")

    return 0
