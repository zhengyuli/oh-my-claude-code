"""
Confidence calculation with time-based decay.

This module provides functions for calculating effective confidence
scores based on time decay, allowing instincts to fade if not reinforced.

The decay mechanism ensures that instincts that are not observed over time
will gradually lose confidence, allowing the system to focus on recently
reinforced patterns.

Constants:
    DEFAULT_DECAY_RATE: 0.02 (2% decay per week)
    MIN_CONFIDENCE: 0.3 (minimum confidence floor)
"""

from datetime import datetime

# Default settings
DEFAULT_DECAY_RATE = 0.02  # Weekly decay rate (2% per week)
MIN_CONFIDENCE = 0.3  # Floor for decayed confidence


def calculate_effective_confidence(
    instinct: dict,
    decay_rate: float = DEFAULT_DECAY_RATE
) -> float:
    """Calculate confidence with time-based decay.

    Decay is applied at decision time based on last_observed timestamp.
    This allows reinforcement when patterns reoccur.

    The decay formula is:
        effective = base_confidence - (decay_rate * weeks_since_last_observed)

    Args:
        instinct: Instinct dict with confidence and last_observed fields
        decay_rate: Weekly decay rate (default 0.02 = 2% per week)

    Returns:
        Effective confidence after decay (floored at MIN_CONFIDENCE)

    Examples:
        >>> instinct = {'confidence': 0.8, 'last_observed': '2026-02-01T00:00:00Z'}
        >>> # Assuming 4 weeks have passed
        >>> effective = calculate_effective_confidence(instinct, decay_rate=0.02)
        >>> # Returns: 0.72 (0.8 - 0.02*4)
    """
    base_confidence = instinct.get('confidence', 0.5)
    # Fall back to created timestamp if last_observed is missing
    last_observed = instinct.get('last_observed', instinct.get('created', ''))

    if not last_observed:
        return base_confidence

    try:
        # Parse ISO timestamp - handle both Z suffix and +/-HH:MM formats
        last_str = last_observed.replace('Z', '+00:00')
        # Add timezone if missing
        if '+' not in last_str and '-' not in last_str[-6:]:
            last_str = last_str + '+00:00'
        last = datetime.fromisoformat(last_str)
        # Use the same timezone for current time
        now = datetime.now(last.tzinfo) if last.tzinfo else datetime.now()

        # Calculate weeks since last observation
        delta = now - last
        weeks_since = max(0, delta.days / 7)

        # Apply decay and floor at minimum confidence
        decay = decay_rate * weeks_since
        return max(MIN_CONFIDENCE, base_confidence - decay)
    except (ValueError, TypeError):
        # On parsing errors, return base confidence
        return base_confidence
