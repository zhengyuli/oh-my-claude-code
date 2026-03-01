"""
Comprehensive confidence decay calculation tests.

This module provides detailed testing of the confidence decay algorithm
to achieve 90%+ coverage for the confidence module.
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.confidence import (
    calculate_effective_confidence,
    DEFAULT_DECAY_RATE,
    MIN_CONFIDENCE
)


@pytest.mark.unit
class TestConfidenceDecayCalculation:
    """Comprehensive tests for confidence decay calculation."""

    def test_no_decay_for_recent_observation(self):
        """Test that recent observations have no significant decay."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(hours=12)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # Less than 1 day should have minimal decay
        assert result >= 0.79

    def test_one_week_exact_decay(self):
        """Test decay after exactly one week."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # 0.8 - (0.02 * 1) = 0.78
        assert result == pytest.approx(0.78, abs=0.01)

    def test_four_weeks_decay(self):
        """Test decay after four weeks."""
        instinct = {
            'confidence': 0.9,
            'last_observed': (datetime.now() - timedelta(weeks=4)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # 0.9 - (0.02 * 4) = 0.82
        assert result == pytest.approx(0.82, abs=0.01)

    def test_decay_floors_at_minimum(self):
        """Test that decay never goes below MIN_CONFIDENCE."""
        instinct = {
            'confidence': 0.5,
            'last_observed': (datetime.now() - timedelta(weeks=52)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # 0.5 - (0.02 * 52) = -0.54, should floor at 0.3
        assert result == MIN_CONFIDENCE

    def test_custom_decay_rate(self):
        """Test with custom decay rate."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=2)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.05)
        # 0.8 - (0.05 * 2) = 0.7
        assert result == pytest.approx(0.70, abs=0.01)

    def test_zero_decay_rate(self):
        """Test with zero decay rate."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=10)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.0)
        assert result == 0.8

    def test_high_decay_rate(self):
        """Test with high decay rate."""
        # Use a fixed timestamp for consistency
        past_time = datetime.now() - timedelta(days=14)
        instinct = {
            'confidence': 0.9,
            'last_observed': past_time.isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.2)
        # 0.9 - (0.2 * 2) ≈ 0.5 (with some tolerance for datetime precision)
        assert 0.48 <= result <= 0.54

    def test_missing_last_observed_field(self):
        """Test with missing last_observed field falls back to created."""
        instinct = {
            'confidence': 0.8,
            'created': '2026-01-01T00:00:00Z'
        }
        result = calculate_effective_confidence(instinct)
        # Should fall back to created field and apply decay
        # Result will be decayed from old created date
        assert result <= 0.8  # Should be decayed

    def test_empty_last_observed_value(self):
        """Test with empty last_observed value."""
        instinct = {
            'confidence': 0.8,
            'last_observed': ''
        }
        result = calculate_effective_confidence(instinct)
        assert result == 0.8

    def test_iso_timestamp_with_zulu(self):
        """Test ISO timestamp with Z suffix."""
        instinct = {
            'confidence': 0.8,
            'last_observed': '2026-02-01T10:00:00Z'
        }
        result = calculate_effective_confidence(instinct)
        # Should parse without error
        assert isinstance(result, float)

    def test_iso_timestamp_with_timezone(self):
        """Test ISO timestamp with explicit timezone."""
        instinct = {
            'confidence': 0.8,
            'last_observed': '2026-02-01T10:00:00+05:00'
        }
        result = calculate_effective_confidence(instinct)
        # Should parse without error
        assert isinstance(result, float)

    def test_invalid_timestamp_format(self):
        """Test with invalid timestamp format."""
        instinct = {
            'confidence': 0.8,
            'last_observed': 'not-a-timestamp'
        }
        result = calculate_effective_confidence(instinct)
        # Should return base confidence on error
        assert result == 0.8

    def test_none_timestamp(self):
        """Test with None as timestamp."""
        instinct = {
            'confidence': 0.8,
            'last_observed': None
        }
        result = calculate_effective_confidence(instinct)
        assert result == 0.8

    def test_missing_confidence_field(self):
        """Test with missing confidence field."""
        instinct = {
            'last_observed': (datetime.now() - timedelta(weeks=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct)
        # Should use default 0.5
        assert result == pytest.approx(0.48, abs=0.05)

    def test_edge_case_just_below_minimum(self):
        """Test confidence just above minimum before decay."""
        instinct = {
            'confidence': 0.31,
            'last_observed': (datetime.now() - timedelta(weeks=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # Should floor at 0.3
        assert result == MIN_CONFIDENCE

    def test_partial_week_decay(self):
        """Test decay for partial week (3.5 days)."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(days=3.5)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        # 0.8 - (0.02 * 0.5) = 0.79
        assert result == pytest.approx(0.79, abs=0.01)

    def test_maximum_confidence_no_decay(self):
        """Test maximum confidence (1.0) with recent observation."""
        instinct = {
            'confidence': 1.0,
            'last_observed': datetime.now().isoformat()
        }
        result = calculate_effective_confidence(instinct)
        assert result == 1.0

    def test_minimum_confidence_no_decay(self):
        """Test minimum confidence (0.3)."""
        instinct = {
            'confidence': MIN_CONFIDENCE,
            'last_observed': (datetime.now() - timedelta(weeks=10)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.1)
        # Should stay at minimum
        assert result == MIN_CONFIDENCE

    def test_decay_table_accuracy(self):
        """Verify decay calculation table accuracy."""
        test_cases = [
            # (base_confidence, weeks_ago, decay_rate, expected)
            (0.9, 1, 0.02, 0.88),
            (0.9, 5, 0.02, 0.80),
            (0.5, 10, 0.02, 0.30),  # floors at 0.3
            (0.3, 100, 0.02, 0.30),  # stays at minimum
        ]

        for base, weeks, rate, expected in test_cases:
            instinct = {
                'confidence': base,
                'last_observed': (datetime.now() - timedelta(weeks=weeks)).isoformat()
            }
            result = calculate_effective_confidence(instinct, decay_rate=rate)
            assert result == pytest.approx(expected, abs=0.01), \
                f"Failed for base={base}, weeks={weeks}, rate={rate}"

    def test_future_timestamp(self):
        """Test with future timestamp (shouldn't decay)."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() + timedelta(days=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct)
        # Future timestamps result in negative weeks, treated as 0
        assert result == 0.8
