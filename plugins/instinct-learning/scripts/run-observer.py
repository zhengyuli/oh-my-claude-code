#!/usr/bin/env python3
"""
Run Observer Analysis

Executes pattern detection and instinct creation.
Called by start-observer.sh periodically.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add lib to path
PLUGIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / 'lib'))

from pattern_detection import load_observations, detect_all_patterns, Pattern
from instinct_parser import (
    Instinct, load_all_instincts, save_instinct,
    generate_instinct_id, update_instinct_evidence
)
from confidence import calculate_confidence, ConfidenceFactors

# Support plugin-specific environment variable
DATA_DIR = Path(os.environ.get('INSTINCT_LEARNING_DATA_DIR', Path.home() / '.claude' / 'instinct-learning'))

# Default configuration
DEFAULT_MAX_PATTERNS_PER_CYCLE = 10


def load_config() -> dict:
    """Load configuration from config.json."""
    config_file = DATA_DIR / 'config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def pattern_to_instinct(pattern: Pattern) -> Instinct:
    """Convert a detected pattern to an instinct."""
    # Generate ID from pattern
    if isinstance(pattern.pattern, list):
        pattern_str = '-'.join(pattern.pattern[:3])
    else:
        pattern_str = str(pattern.pattern)

    instinct_id = generate_instinct_id(pattern_str, pattern.domain)

    # Build trigger description
    if pattern.pattern_type == 'repeated_sequence':
        trigger = f"when using {' → '.join(pattern.pattern)} sequence"
    elif pattern.pattern_type == 'error_fix':
        trigger = f"when {pattern.pattern} error occurs"
    elif pattern.pattern_type == 'tool_preference':
        trigger = f"when choosing tools"
    else:
        trigger = f"when {pattern.pattern}"

    # Build action
    action = f"Apply learned {pattern.pattern_type.replace('_', ' ')} pattern"

    # Build evidence
    evidence = [f"Detected in {pattern.evidence_count} observations"]

    return Instinct(
        id=instinct_id,
        trigger=trigger,
        confidence=pattern.confidence,
        domain=pattern.domain,
        created=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        source='observation',
        evidence_count=pattern.evidence_count,
        action=action,
        evidence=evidence
    )


def run_observer():
    """Run the observer analysis cycle."""
    print(f"[{datetime.utcnow().isoformat()}] Starting observer cycle")

    # Load configuration
    config = load_config()
    max_patterns = int(os.environ.get('INSTINCT_MAX_PATTERNS',
        config.get('observer', {}).get('max_patterns_per_cycle', DEFAULT_MAX_PATTERNS_PER_CYCLE)))

    # Load observations
    obs_file = DATA_DIR / 'observations.jsonl'
    observations = load_observations(obs_file)

    if not observations:
        print("No observations to analyze")
        return

    print(f"Loaded {len(observations)} observations")

    # Detect patterns
    patterns = detect_all_patterns(observations)
    print(f"Detected {len(patterns)} patterns")

    if not patterns:
        return

    # Load existing instincts
    existing_instincts = load_all_instincts(DATA_DIR)
    existing_by_trigger = {i.trigger: i for i in existing_instincts}

    # Create or update instincts
    new_count = 0
    updated_count = 0

    for pattern in patterns[:max_patterns]:  # Use configurable limit
        # Build trigger - handle both string and list patterns
        if isinstance(pattern.pattern, list):
            trigger = f"when using {' → '.join(pattern.pattern)} sequence"
        elif isinstance(pattern.pattern, str) and pattern.pattern.startswith('when'):
            trigger = pattern.pattern
        else:
            trigger = f"when {pattern.pattern}"

        if trigger in existing_by_trigger:
            # Update existing instinct
            instinct = existing_by_trigger[trigger]
            instinct = update_instinct_evidence(
                instinct,
                f"Reconfirmed at {datetime.utcnow().isoformat()}"
            )
            save_instinct(instinct, DATA_DIR, 'personal')
            updated_count += 1
        else:
            # Create new instinct
            instinct = pattern_to_instinct(pattern)
            save_instinct(instinct, DATA_DIR, 'personal')
            new_count += 1

    print(f"Created {new_count} new instincts, updated {updated_count}")

    # Check for evolution opportunities
    all_instincts = load_all_instincts(DATA_DIR)
    from clustering import create_clusters

    clusters = create_clusters(all_instincts)
    ready = [c for c in clusters if c.avg_confidence >= 0.7 and c.count >= 3]

    if ready:
        print(f"Evolution opportunities: {len(ready)} domains ready")
        for cluster in ready:
            print(f"  - {cluster.domain}: {cluster.count} instincts (avg {cluster.avg_confidence:.2f})")


if __name__ == '__main__':
    try:
        run_observer()
    except Exception as e:
        print(f"Observer error: {e}", file=sys.stderr)
        sys.exit(1)
