"""Edge case tests for confidence calculation."""
import pytest
from datetime import datetime, timedelta
from scripts.utils.confidence import calculate_effective_confidence, MIN_CONFIDENCE


def test_confidence_with_missing_timestamp():
    """Missing timestamps should return base confidence."""
    instinct = {'confidence': 0.8}
    # No last_observed or created field
    result = calculate_effective_confidence(instinct)
    assert result == 0.8


def test_confidence_with_missing_last_observed_but_has_created():
    """Should fall back to created timestamp when last_observed is missing."""
    old_date = (datetime.now() - timedelta(days=30)).isoformat()
    instinct = {
        'confidence': 0.8,
        'created': old_date
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.05)
    # Should decay based on created timestamp
    assert result < 0.8
    assert result >= MIN_CONFIDENCE


def test_confidence_floor_at_minimum():
    """Confidence should not decay below MIN_CONFIDENCE."""
    # Instinct from 1 year ago
    old_date = (datetime.now() - timedelta(days=365)).isoformat()
    instinct = {
        'confidence': 0.9,
        'last_observed': old_date
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.1)
    # Should floor at 0.3
    assert result >= MIN_CONFIDENCE
    assert result == MIN_CONFIDENCE


def test_confidence_with_invalid_timestamp():
    """Invalid timestamps should return base confidence."""
    instinct = {
        'confidence': 0.7,
        'last_observed': 'invalid-date'
    }
    result = calculate_effective_confidence(instinct)
    assert result == 0.7


def test_confidence_with_empty_timestamp():
    """Empty timestamp strings should return base confidence."""
    instinct = {
        'confidence': 0.75,
        'last_observed': ''
    }
    result = calculate_effective_confidence(instinct)
    assert result == 0.75


def test_confidence_with_none_timestamp():
    """None timestamp should return base confidence."""
    instinct = {
        'confidence': 0.85,
        'last_observed': None
    }
    result = calculate_effective_confidence(instinct)
    assert result == 0.85


def test_confidence_no_decay_for_recent():
    """Recent instincts should not decay."""
    # Instinct from today
    today = datetime.now().isoformat()
    instinct = {
        'confidence': 0.8,
        'last_observed': today
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.02)
    # Should be very close to base confidence (minimal decay)
    assert result >= 0.79


def test_confidence_with_z_suffix():
    """Should handle timestamps with Z suffix (UTC)."""
    # Timestamp with Z suffix
    old_date = (datetime.now() - timedelta(days=14)).replace(microsecond=0)
    timestamp = old_date.isoformat() + 'Z'
    instinct = {
        'confidence': 0.8,
        'last_observed': timestamp
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.02)
    # Should decay for 2 weeks
    expected = max(MIN_CONFIDENCE, 0.8 - (0.02 * 2))
    assert abs(result - expected) < 0.01


def test_confidence_with_timezone_offset():
    """Should handle timestamps with timezone offset."""
    # Timestamp with timezone offset
    old_date = (datetime.now() - timedelta(days=7)).replace(microsecond=0)
    timestamp = old_date.isoformat() + '+05:30'
    instinct = {
        'confidence': 0.8,
        'last_observed': timestamp
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.02)
    # Should decay for 1 week
    expected = max(MIN_CONFIDENCE, 0.8 - (0.02 * 1))
    assert abs(result - expected) < 0.01


def test_confidence_missing_confidence_field():
    """Should default to 0.5 when confidence field is missing."""
    instinct = {'last_observed': datetime.now().isoformat()}
    result = calculate_effective_confidence(instinct)
    assert result == 0.5


def test_confidence_zero_decay_rate():
    """Zero decay rate should return base confidence."""
    old_date = (datetime.now() - timedelta(days=365)).isoformat()
    instinct = {
        'confidence': 0.8,
        'last_observed': old_date
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.0)
    assert result == 0.8


def test_confidence_high_decay_rate():
    """High decay rate should floor quickly."""
    old_date = (datetime.now() - timedelta(days=14)).isoformat()
    instinct = {
        'confidence': 0.9,
        'last_observed': old_date
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.5)
    # Should decay heavily but floor at MIN_CONFIDENCE
    assert result >= MIN_CONFIDENCE
