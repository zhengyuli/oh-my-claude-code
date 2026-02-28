#!/usr/bin/env python3
"""
Pattern Detection Library

Detects behavioral patterns from observation records.
"""

import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Pattern:
    """Represents a detected pattern."""
    pattern_type: str
    pattern: str | list[str]
    confidence: float
    evidence_count: int
    domain: str
    evidence: list[dict]


def load_observations(file_path: Path) -> list[dict]:
    """Load observations from JSONL file."""
    observations = []
    if not file_path.exists():
        return observations

    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    observations.append(json.loads(line))
                except json.JSONDecodeError as e:
                    # Log malformed line but continue processing
                    print(f"Warning: Malformed JSON at line {line_num}: {e}", file=sys.stderr)
                    continue
    return observations


def extract_tool_sequences(observations: list[dict], min_length: int = 2) -> dict[tuple[str, ...], int]:
    """Extract tool usage sequences from observations."""
    sequences = Counter()

    # Group by session
    by_session = defaultdict(list)
    for obs in observations:
        session = obs.get('session', 'default')
        by_session[session].append(obs)

    # Extract sequences from each session
    for session_obs in by_session.values():
        # Sort by timestamp
        sorted_obs = sorted(session_obs, key=lambda x: x.get('timestamp', ''))

        # Extract tool names in order
        tools = [obs.get('tool', '') for obs in sorted_obs if obs.get('tool')]

        # Find sequences of length min_length to 5
        for length in range(min_length, min(6, len(tools) + 1)):
            for i in range(len(tools) - length + 1):
                seq = tuple(tools[i:i + length])
                sequences[seq] += 1

    return dict(sequences)


def detect_repeated_sequences(
    observations: list[dict],
    min_occurrences: int = 3
) -> list[Pattern]:
    """Detect repeated tool usage sequences."""
    patterns = []
    sequences = extract_tool_sequences(observations)

    for seq, count in sequences.items():
        if count >= min_occurrences:
            # Determine domain from tools
            domain = infer_domain_from_sequence(seq)

            patterns.append(Pattern(
                pattern_type='repeated_sequence',
                pattern=list(seq),
                confidence=calculate_sequence_confidence(count),
                evidence_count=count,
                domain=domain,
                evidence=[{'sequence': list(seq), 'count': count}]
            ))

    return patterns


def detect_error_fix_patterns(observations: list[dict]) -> list[Pattern]:
    """Detect error followed by fix patterns."""
    patterns = []

    # Group by session
    by_session = defaultdict(list)
    for obs in observations:
        session = obs.get('session', 'default')
        by_session[session].append(obs)

    error_fix_pairs = Counter()

    for session_obs in by_session.values():
        sorted_obs = sorted(session_obs, key=lambda x: x.get('timestamp', ''))

        for i, obs in enumerate(sorted_obs):
            # Look for failed tool calls
            if obs.get('exit_code') and obs.get('exit_code') != '0':
                failed_tool = obs.get('tool', '')

                # Look for subsequent successful calls
                for j in range(i + 1, min(i + 5, len(sorted_obs))):
                    next_obs = sorted_obs[j]
                    if next_obs.get('exit_code') == '0' or next_obs.get('type') == 'post_tool':
                        success_tool = next_obs.get('tool', '')
                        if success_tool:
                            pair = (failed_tool, success_tool)
                            error_fix_pairs[pair] += 1
                            break

    for (failed, success), count in error_fix_pairs.items():
        if count >= 2:
            patterns.append(Pattern(
                pattern_type='error_fix',
                pattern=f"{failed} → {success}",
                confidence=0.7,  # Error-fix patterns have good confidence
                evidence_count=count,
                domain='debugging',
                evidence=[{'failed_tool': failed, 'recovery_tool': success, 'count': count}]
            ))

    return patterns


def detect_tool_preferences(observations: list[dict]) -> list[Pattern]:
    """Detect tool usage preferences."""
    patterns = []

    # Count tool usage
    tool_counts = Counter()
    for obs in observations:
        tool = obs.get('tool', '')
        if tool:
            tool_counts[tool] += 1

    total_tools = sum(tool_counts.values())
    if total_tools == 0:
        return patterns

    # Find dominant tools (>20% usage)
    for tool, count in tool_counts.most_common(10):
        ratio = count / total_tools
        if ratio > 0.2 and count >= 5:
            patterns.append(Pattern(
                pattern_type='tool_preference',
                pattern=f"Prefer {tool}",
                confidence=min(0.9, 0.5 + ratio),
                evidence_count=count,
                domain='workflow',
                evidence=[{'tool': tool, 'usage_ratio': ratio, 'count': count}]
            ))

    return patterns


def infer_domain_from_sequence(sequence: tuple[str, ...]) -> str:
    """Infer domain from a tool sequence."""
    tool_to_domain = {
        'Edit': 'code-style',
        'Write': 'code-style',
        'Read': 'workflow',
        'Grep': 'debugging',
        'Glob': 'workflow',
        'Bash': 'workflow'
    }

    # Count domain occurrences
    domain_counts = Counter()
    for tool in sequence:
        domain = tool_to_domain.get(tool, 'workflow')
        domain_counts[domain] += 1

    # Return most common domain
    return domain_counts.most_common(1)[0][0] if domain_counts else 'workflow'


def calculate_sequence_confidence(count: int) -> float:
    """Calculate confidence based on occurrence count."""
    if count >= 10:
        return 0.9
    elif count >= 5:
        return 0.7
    elif count >= 3:
        return 0.5
    else:
        return 0.3


def detect_all_patterns(observations: list[dict]) -> list[Pattern]:
    """Run all pattern detection algorithms."""
    all_patterns = []

    # Detect different pattern types
    all_patterns.extend(detect_repeated_sequences(observations))
    all_patterns.extend(detect_error_fix_patterns(observations))
    all_patterns.extend(detect_tool_preferences(observations))

    # Sort by confidence
    all_patterns.sort(key=lambda p: p.confidence, reverse=True)

    return all_patterns


def group_patterns_by_domain(patterns: list[Pattern]) -> dict[str, list[Pattern]]:
    """Group patterns by domain."""
    grouped = defaultdict(list)
    for pattern in patterns:
        grouped[pattern.domain].append(pattern)
    return dict(grouped)


if __name__ == '__main__':
    # Test with sample data
    import sys

    # Support plugin-specific environment variable
    data_dir = Path(os.environ.get('INSTINCT_LEARNING_DATA_DIR', Path.home() / '.claude' / 'instinct-learning'))
    obs_file = data_dir / 'observations.jsonl'

    if obs_file.exists():
        observations = load_observations(obs_file)
        patterns = detect_all_patterns(observations)

        print(f"Detected {len(patterns)} patterns:")
        for p in patterns[:10]:
            print(f"  [{p.confidence:.1f}] {p.pattern_type}: {p.pattern}")
    else:
        print(f"No observations file found at {obs_file}")
