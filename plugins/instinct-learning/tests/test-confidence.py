#!/usr/bin/env python3
"""
Unit tests for confidence calculation library.
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from confidence import (
    ConfidenceFactors,
    ConfidenceManager,
    calculate_base_confidence,
    apply_corrections,
    apply_consistency_boost,
    calculate_confidence,
    get_confidence_level,
    should_auto_apply,
    calculate_decay,
    calculate_merge_confidence,
    calculate_cluster_confidence,
    MIN_CONFIDENCE,
    MAX_CONFIDENCE,
    AUTO_APPROVE_THRESHOLD
)


class TestCalculateBaseConfidence(unittest.TestCase):
    """Tests for calculate_base_confidence function."""

    def test_less_than_3_occurrences(self):
        """Test that <3 occurrences returns minimum confidence."""
        self.assertEqual(calculate_base_confidence(0), MIN_CONFIDENCE)
        self.assertEqual(calculate_base_confidence(1), MIN_CONFIDENCE)
        self.assertEqual(calculate_base_confidence(2), MIN_CONFIDENCE)

    def test_3_to_4_occurrences(self):
        """Test 3-4 occurrences returns 0.5."""
        self.assertEqual(calculate_base_confidence(3), 0.5)
        self.assertEqual(calculate_base_confidence(4), 0.5)

    def test_5_to_9_occurrences(self):
        """Test 5-9 occurrences returns 0.6."""
        self.assertEqual(calculate_base_confidence(5), 0.6)
        self.assertEqual(calculate_base_confidence(9), 0.6)

    def test_10_plus_occurrences(self):
        """Test 10+ occurrences returns 0.8."""
        self.assertEqual(calculate_base_confidence(10), 0.8)
        self.assertEqual(calculate_base_confidence(20), 0.8)


class TestApplyCorrections(unittest.TestCase):
    """Tests for apply_corrections function."""

    def test_no_corrections(self):
        """Test no corrections doesn't change confidence."""
        base = 0.7
        result = apply_corrections(base, 0)
        self.assertEqual(result, base)

    def test_single_correction(self):
        """Test one correction reduces confidence by 0.15."""
        base = 0.7
        result = apply_corrections(base, 1)
        self.assertAlmostEqual(result, 0.55, places=1)

    def test_multiple_corrections(self):
        """Test multiple corrections accumulate penalty."""
        base = 0.8
        result = apply_corrections(base, 2)
        self.assertEqual(result, 0.5)

    def test_corrections_dont_go_below_minimum(self):
        """Test corrections never go below MIN_CONFIDENCE."""
        base = MIN_CONFIDENCE
        result = apply_corrections(base, 10)
        self.assertEqual(result, MIN_CONFIDENCE)


class TestApplyConsistencyBoost(unittest.TestCase):
    """Tests for apply_consistency_boost function."""

    def test_no_boost_low_consistency(self):
        """Test low consistency (<0.7) gives no boost."""
        base = 0.6
        result = apply_consistency_boost(base, 0.5)
        self.assertEqual(result, base)

    def test_moderate_boost(self):
        """Test consistency 0.7-0.9 gives 0.05 boost."""
        base = 0.6
        result = apply_consistency_boost(base, 0.8)
        self.assertEqual(result, 0.65)

    def test_high_boost(self):
        """Test consistency >0.9 gives 0.1 boost."""
        base = 0.7
        result = apply_consistency_boost(base, 0.95)
        self.assertAlmostEqual(result, 0.8, places=1)

    def test_boost_doesnt_exceed_max(self):
        """Test boost never exceeds MAX_CONFIDENCE."""
        base = MAX_CONFIDENCE
        result = apply_consistency_boost(base, 1.0)
        self.assertEqual(result, MAX_CONFIDENCE)


class TestCalculateConfidence(unittest.TestCase):
    """Tests for calculate_confidence function."""

    def test_minimal_occurrences(self):
        """Test confidence with minimal data."""
        factors = ConfidenceFactors(occurrence_count=1)
        result = calculate_confidence(factors)
        # Base is 0.3 + 0.1 consistency boost = 0.4
        self.assertEqual(result, 0.4)

    def test_occurrences_boost_confidence(self):
        """Test more occurrences increase confidence."""
        factors_low = ConfidenceFactors(occurrence_count=3)
        factors_high = ConfidenceFactors(occurrence_count=10)

        result_low = calculate_confidence(factors_low)
        result_high = calculate_confidence(factors_high)

        self.assertGreater(result_high, result_low)

    def test_corrections_reduce_confidence(self):
        """Test user corrections reduce confidence."""
        factors_no_corr = ConfidenceFactors(occurrence_count=5)
        factors_with_corr = ConfidenceFactors(occurrence_count=5, user_corrections=2)

        result_no = calculate_confidence(factors_no_corr)
        result_with = calculate_confidence(factors_with_corr)

        self.assertLess(result_with, result_no)

    def test_full_factors(self):
        """Test confidence with all factors combined."""
        factors = ConfidenceFactors(
            occurrence_count=5,
            user_corrections=1,
            consistency_score=0.8,
            recency_boost=0.0,
            domain_relevance=1.0
        )
        result = calculate_confidence(factors)

        # Should be: 0.6 (base) - 0.15 (correction) + 0.05 (consistency) = 0.5
        self.assertAlmostEqual(result, 0.5, places=1)


class TestGetConfidenceLevel(unittest.TestCase):
    """Tests for get_confidence_level function."""

    def test_high_confidence(self):
        """Test confidence >=0.7 returns 'high'."""
        self.assertEqual(get_confidence_level(0.7), 'high')
        self.assertEqual(get_confidence_level(0.9), 'high')

    def test_medium_confidence(self):
        """Test confidence 0.5-0.7 returns 'medium'."""
        self.assertEqual(get_confidence_level(0.5), 'medium')
        self.assertEqual(get_confidence_level(0.6), 'medium')

    def test_low_confidence(self):
        """Test confidence <0.5 returns 'low'."""
        self.assertEqual(get_confidence_level(0.3), 'low')
        self.assertEqual(get_confidence_level(0.49), 'low')


class TestShouldAutoApply(unittest.TestCase):
    """Tests for should_auto_apply function."""

    def test_below_threshold(self):
        """Test confidence below 0.7 should not auto-apply."""
        self.assertFalse(should_auto_apply(0.5))
        self.assertFalse(should_auto_apply(0.69))

    def test_at_threshold(self):
        """Test confidence at 0.7 should auto-apply."""
        self.assertTrue(should_auto_apply(0.7))

    def test_above_threshold(self):
        """Test confidence above 0.7 should auto-apply."""
        self.assertTrue(should_auto_apply(0.8))
        self.assertTrue(should_auto_apply(0.9))


class TestCalculateDecay(unittest.TestCase):
    """Tests for calculate_decay function."""

    def test_no_decay_same_day(self):
        """Test no decay for same day."""
        result = calculate_decay(0.7, days_since_use=0, decay_rate=0.02)
        self.assertEqual(result, 0.7)

    def test_one_day_decay(self):
        """Test one day of decay."""
        result = calculate_decay(0.7, days_since_use=1, decay_rate=0.02)
        self.assertAlmostEqual(result, 0.68, places=2)

    def test_decay_respects_minimum(self):
        """Test decay never goes below MIN_CONFIDENCE."""
        result = calculate_decay(MIN_CONFIDENCE, days_since_use=100, decay_rate=0.02)
        self.assertEqual(result, MIN_CONFIDENCE)

    def test_extended_decay(self):
        """Test decay over many days."""
        result = calculate_decay(0.9, days_since_use=10, decay_rate=0.02)
        # 0.9 - (10 * 0.02) = 0.7
        self.assertEqual(result, 0.7)


class TestCalculateMergeConfidence(unittest.TestCase):
    """Tests for calculate_merge_confidence function."""

    def test_equal_weight_merge(self):
        """Test merging with equal weights."""
        result = calculate_merge_confidence(0.6, 0.8, weight1=0.5)
        self.assertEqual(result, 0.7)

    def test_unequal_weight_merge(self):
        """Test merging with unequal weights."""
        result = calculate_merge_confidence(0.6, 0.8, weight1=0.75)
        # 0.6 * 0.75 + 0.8 * 0.25 = 0.45 + 0.2 = 0.65
        self.assertEqual(result, 0.65)

    def test_merge_respects_bounds(self):
        """Test merge result stays within bounds."""
        # Both high
        result = calculate_merge_confidence(0.9, 0.9, weight1=0.5)
        self.assertLessEqual(result, MAX_CONFIDENCE)

        # Both low
        result = calculate_merge_confidence(MIN_CONFIDENCE, MIN_CONFIDENCE, weight1=0.5)
        self.assertGreaterEqual(result, MIN_CONFIDENCE)


class TestCalculateClusterConfidence(unittest.TestCase):
    """Tests for calculate_cluster_confidence function."""

    def test_single_instinct(self):
        """Test cluster with one instinct."""
        result = calculate_cluster_confidence([0.7])
        # 0.7 + 0.02 boost (1 * 0.02) = 0.72
        self.assertAlmostEqual(result, 0.72, places=2)

    def test_multiple_instincts(self):
        """Test cluster with multiple instincts."""
        result = calculate_cluster_confidence([0.6, 0.7, 0.8])
        # avg = 0.7, boost = 3 * 0.02 = 0.06, total = 0.76
        self.assertAlmostEqual(result, 0.76, places=2)

    def test_cluster_boost(self):
        """Test that larger clusters get a boost."""
        two_instincts = calculate_cluster_confidence([0.7, 0.7])
        five_instincts = calculate_cluster_confidence([0.7, 0.7, 0.7, 0.7, 0.7])

        # Five instincts should have higher confidence due to cluster boost
        self.assertGreater(five_instincts, two_instincts)


class TestConfidenceManager(unittest.TestCase):
    """Tests for ConfidenceManager class."""

    def test_record_use(self):
        """Test recording instinct use updates last_used."""
        manager = ConfidenceManager()
        instinct_id = 'test-instinct'

        manager.record_use(instinct_id)

        self.assertIn(instinct_id, manager.last_used)
        self.assertIsInstance(manager.last_used[instinct_id], datetime)

    def test_record_correction(self):
        """Test recording correction increments count."""
        manager = ConfidenceManager()
        instinct_id = 'test-instinct'

        manager.record_correction(instinct_id)
        manager.record_correction(instinct_id)

        self.assertEqual(manager.corrections[instinct_id], 2)

    def test_get_adjusted_confidence(self):
        """Test getting adjusted confidence with corrections."""
        manager = ConfidenceManager()
        instinct_id = 'test-instinct'

        # Record a correction
        manager.record_correction(instinct_id)

        # Get adjusted confidence
        adjusted = manager.get_adjusted_confidence(instinct_id, 0.7)

        # Should be reduced due to correction
        self.assertLess(adjusted, 0.7)
        self.assertGreaterEqual(adjusted, MIN_CONFIDENCE)


if __name__ == '__main__':
    unittest.main()
