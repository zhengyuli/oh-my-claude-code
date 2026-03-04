"""Status command handler.

Displays learned instincts with confidence scores, domain groupings,
and system statistics. Shows confidence bars (█/░) and action snippets.
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
    """Display all learned instincts with confidence scores."""
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

            # Extract action snippet
            content = inst.get('content', '')
            match = re.search(r'## Action\s*\n\s*(.+?)(?:\n\n|\n##|$)', content, re.DOTALL)
            if match:
                action = match.group(1).strip().split('\n')[0]
                action = action[:60] + '...' if len(action) > 60 else action
                print(f"            action: {action}")
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
