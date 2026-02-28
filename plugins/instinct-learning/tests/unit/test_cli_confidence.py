# tests/unit/test_cli_confidence.py
import pytest
from datetime import datetime, timedelta
from instinct_cli import calculate_effective_confidence

@pytest.mark.unit
class TestCalculateEffectiveConfidence:
    """Tests for confidence decay calculation."""

    def test_no_decay_when_recent(self):
        """Test no decay for recent observations."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(days=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        assert result == 0.8  # No significant decay after 1 day

    def test_one_week_decay(self):
        """Test decay after one week."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        assert result == pytest.approx(0.78, abs=0.01)  # 0.8 - 0.02

    def test_multiple_weeks_decay(self):
        """Test decay after multiple weeks."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=3)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        assert result == pytest.approx(0.74, abs=0.01)  # 0.8 - (0.02 * 3)

    def test_confidence_floor_at_0_3(self):
        """Test that confidence never goes below 0.3."""
        instinct = {
            'confidence': 0.5,
            'last_observed': (datetime.now() - timedelta(weeks=100)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.02)
        assert result == 0.3  # Floor value

    def test_missing_last_observed_returns_base(self):
        """Test that missing last_observed returns base confidence."""
        instinct = {'confidence': 0.7}
        result = calculate_effective_confidence(instinct)
        assert result == 0.7

    def test_missing_confidence_defaults_to_0_5(self):
        """Test that missing confidence defaults to 0.5."""
        instinct = {'last_observed': datetime.now().isoformat()}
        result = calculate_effective_confidence(instinct)
        assert result == 0.5

    def test_invalid_timestamp_returns_base(self):
        """Test that invalid timestamp returns base confidence."""
        instinct = {
            'confidence': 0.7,
            'last_observed': 'invalid-timestamp'
        }
        result = calculate_effective_confidence(instinct)
        assert result == 0.7

    def test_custom_decay_rate(self):
        """Test custom decay rate."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=1)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.05)
        assert result == pytest.approx(0.75, abs=0.01)  # 0.8 - 0.05

    def test_zero_decay_rate(self):
        """Test zero decay rate."""
        instinct = {
            'confidence': 0.8,
            'last_observed': (datetime.now() - timedelta(weeks=10)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.0)
        assert result == 0.8

    @pytest.mark.parametrize("base,weeks,decay_rate,expected", [
        (0.9, 1, 0.02, 0.88),
        (0.9, 5, 0.02, 0.8),
        (0.5, 10, 0.02, 0.3),  # Hits floor
        (0.3, 100, 0.02, 0.3),  # Stays at floor
    ])
    def test_decay_calculation_table(self, base, weeks, decay_rate, expected):
        """Test decay calculation with various parameters."""
        instinct = {
            'confidence': base,
            'last_observed': (datetime.now() - timedelta(weeks=weeks)).isoformat()
        }
        result = calculate_effective_confidence(instinct, decay_rate=decay_rate)
        assert result == pytest.approx(expected, abs=0.01)
