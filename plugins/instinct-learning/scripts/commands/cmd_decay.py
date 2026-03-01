"""
Decay command handler.

This module displays effective confidence after time-based decay for all
instincts. It helps identify which instincts have become stale due to lack
of recent observations and may need refreshing.

Decay Algorithm:
- Confidence decays at a constant rate per week (default 2%)
- Decay is calculated from the last_observed timestamp
- Formula: effective = base_confidence - (decay_rate * weeks_since_last_observed)
- Effective confidence is capped at a minimum of 0.0

Display Format:
- Sorted by effective confidence (most decayed first)
- Shows base confidence, effective confidence, and decay amount
- Displays last observation timestamp
- Instincts with negligible decay (< 1%) shown as "no decay"

Usage:
    # Show decay with default rate (2%/week)
    $ python3 instinct_cli.py decay

    # Show decay with custom rate (5%/week)
    $ python3 instinct_cli.py decay --decay-rate 0.05

Interpreting Output:
- High decay amounts indicate stale instincts
- Consider refreshing or re-observing patterns with high decay
- Instincts with "no decay" are recently observed and stable
"""

from argparse import Namespace

from utils.file_io import load_all_instincts
from utils.confidence import calculate_effective_confidence, DEFAULT_DECAY_RATE


def cmd_decay(args: Namespace) -> int:
    """Show effective confidence after decay for all instincts.

    This function loads all instincts and calculates their effective
    confidence after applying time-based decay. Results are sorted by
    effective confidence to highlight the most decayed instincts.

    Args:
        args: argparse.Namespace with attributes:
            - decay_rate: Weekly decay rate as float (optional)
                         Uses DEFAULT_DECAY_RATE (0.02) if not provided

    Returns:
        0 on success (displays message if no instincts found)

    Output Format:
        For each instinct with significant decay (> 1%):
            - Instinct ID
            - Base confidence → Effective confidence (decay amount)
            - Last observation timestamp

        For instincts with negligible decay:
            - Instinct ID: Base confidence (no decay)

    Example:
        >>> cmd_decay(Namespace(decay_rate=0.05))
        # Shows decay analysis at 5% per week
        # my-instinct:
        #   Base: 0.80 → Effective: 0.60 (decay: -0.20)
        #   Last observed: 2026-01-15T10:30:00
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
