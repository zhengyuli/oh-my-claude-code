"""
Coverage tests for cmd_prune module.

Tests effective confidence calculation and sorting behavior.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, timedelta

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.confidence import calculate_effective_confidence


@pytest.mark.unit
class TestEffectiveConfidenceSorting:
    """Test effective confidence calculation for sorting."""

    def test_effective_confidence_calculates_decay(self):
        """Test that effective confidence is calculated and used for sorting."""
        old_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
        recent_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        old_instinct = {
            'id': 'old',
            'confidence': 0.8,
            'last_observed': old_date,
            '_source_file': '/fake/old.yaml'
        }
        recent_instinct = {
            'id': 'recent',
            'confidence': 0.8,
            'last_observed': recent_date,
            '_source_file': '/fake/recent.yaml'
        }

        old_effective = calculate_effective_confidence(old_instinct)
        recent_effective = calculate_effective_confidence(recent_instinct)

        # Recent should have higher effective confidence (less decay)
        assert recent_effective > old_effective
        assert old_effective < 0.8  # Should have decayed
        assert recent_effective == 0.8  # Should have no decay

    def test_effective_confidence_capped_at_zero(self):
        """Test that effective confidence is capped at minimum of 0.0."""
        very_old_date = (datetime.now() - timedelta(days=1000)).strftime('%Y-%m-%dT%H:%M:%SZ')

        very_old_instinct = {
            'id': 'very_old',
            'confidence': 0.3,
            'last_observed': very_old_date,
        }

        effective = calculate_effective_confidence(very_old_instinct)
        assert effective >= 0.0

    def test_effective_confidence_with_no_last_observed(self):
        """Test handling of instincts without last_observed timestamp."""
        instinct_no_date = {
            'id': 'no_date',
            'confidence': 0.7,
        }

        effective = calculate_effective_confidence(instinct_no_date)
        # Should return base confidence when no last_observed
        assert effective == 0.7
