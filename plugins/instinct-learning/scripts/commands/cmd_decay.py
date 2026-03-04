"""Decay command handler.

Displays effective confidence after time-based decay. Shows decay amount
and last observation timestamp, sorted by effective confidence.
"""

from argparse import Namespace

from utils.file_io import load_all_instincts
from utils.confidence import calculate_effective_confidence, DEFAULT_DECAY_RATE


def cmd_decay(args: Namespace) -> int:
    """Show effective confidence after decay for all instincts.

    Calculates effective confidence using time-based decay and displays
    results sorted by effective confidence (most decayed first).
    """
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts found.")
        return 0

    decay_rate = args.decay_rate if args.decay_rate is not None else DEFAULT_DECAY_RATE

    # Calculate effective confidence for each instinct
    results = []
    for inst in instincts:
        base = inst.get('confidence', 0.5)
        effective = calculate_effective_confidence(inst, decay_rate)
        decay_amount = base - effective
        results.append({
            'id': inst.get('id', 'unnamed'),
            'base': base,
            'effective': effective,
            'decay': decay_amount,
            'last_observed': inst.get('last_observed', inst.get('created', 'unknown'))
        })

    # Sort by effective confidence (lowest first - most decayed)
    results.sort(key=lambda x: x['effective'])

    # Display results
    print(f"\n{'='*70}")
    print(f"  CONFIDENCE DECAY ANALYSIS (rate: {decay_rate:.2%}/week)")
    print(f"{'='*70}\n")

    for r in results:
        if r['decay'] > 0.01:
            print(f"{r['id']}:")
            decay_info = (
                f"  Base: {r['base']:.2f} → Effective: {r['effective']:.2f} "
                f"(decay: -{r['decay']:.2f})"
            )
            print(decay_info)
            print(f"  Last observed: {r['last_observed']}")
        else:
            print(f"{r['id']}: {r['base']:.2f} (no decay)")

    print(f"\n{'='*70}\n")

    return 0
