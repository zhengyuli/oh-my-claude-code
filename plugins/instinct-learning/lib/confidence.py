#!/usr/bin/env python3
"""
Confidence Calculation Library

Calculates and manages confidence scores for instincts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ConfidenceFactors:
    """Factors affecting confidence calculation."""
    occurrence_count: int = 0
    user_corrections: int = 0
    consistency_score: float = 1.0
    recency_boost: float = 0.0
    domain_relevance: float = 1.0


# Confidence thresholds
MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.9
TENTATIVE_THRESHOLD = 0.5
MODERATE_THRESHOLD = 0.7
AUTO_APPROVE_THRESHOLD = 0.7


def calculate_base_confidence(occurrence_count: int) -> float:
    """Calculate base confidence from occurrence count."""
    if occurrence_count >= 10:
        return 0.8
    elif occurrence_count >= 5:
        return 0.6
    elif occurrence_count >= 3:
        return 0.5
    else:
        return MIN_CONFIDENCE


def apply_corrections(base_confidence: float, correction_count: int) -> float:
    """Reduce confidence based on user corrections."""
    penalty = correction_count * 0.15
    return max(MIN_CONFIDENCE, base_confidence - penalty)


def apply_consistency_boost(confidence: float, consistency_score: float) -> float:
    """Boost confidence based on pattern consistency."""
    if consistency_score > 0.9:
        return min(MAX_CONFIDENCE, confidence + 0.1)
    elif consistency_score > 0.7:
        return min(MAX_CONFIDENCE, confidence + 0.05)
    return confidence


def calculate_confidence(factors: ConfidenceFactors) -> float:
    """Calculate final confidence score from all factors."""
    # Start with base confidence from occurrences
    confidence = calculate_base_confidence(factors.occurrence_count)

    # Apply correction penalty
    confidence = apply_corrections(confidence, factors.user_corrections)

    # Apply consistency boost
    confidence = apply_consistency_boost(confidence, factors.consistency_score)

    # Apply recency boost (patterns observed recently are more relevant)
    confidence = min(MAX_CONFIDENCE, confidence + factors.recency_boost)

    # Apply domain relevance
    confidence *= factors.domain_relevance

    # Ensure within bounds
    return round(max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence)), 2)


def get_confidence_level(confidence: float) -> str:
    """Get human-readable confidence level."""
    if confidence >= AUTO_APPROVE_THRESHOLD:
        return "high"
    elif confidence >= TENTATIVE_THRESHOLD:
        return "medium"
    else:
        return "low"


def should_auto_apply(confidence: float) -> bool:
    """Check if instinct should be auto-applied without confirmation."""
    return confidence >= AUTO_APPROVE_THRESHOLD


def calculate_decay(
    current_confidence: float,
    days_since_use: int,
    decay_rate: float = 0.02
) -> float:
    """Calculate confidence decay for unused instincts."""
    if days_since_use <= 0:
        return current_confidence

    decay_amount = days_since_use * decay_rate
    return max(MIN_CONFIDENCE, current_confidence - decay_amount)


def calculate_merge_confidence(
    confidence1: float,
    confidence2: float,
    weight1: float = 0.5
) -> float:
    """Calculate confidence when merging two instincts."""
    weight2 = 1 - weight1
    merged = (confidence1 * weight1) + (confidence2 * weight2)
    return round(max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, merged)), 2)


def calculate_cluster_confidence(confidences: list[float]) -> float:
    """Calculate average confidence for a cluster of instincts."""
    if not confidences:
        return MIN_CONFIDENCE

    avg = sum(confidences) / len(confidences)
    # Boost slightly for larger clusters
    cluster_boost = min(0.1, len(confidences) * 0.02)
    return round(min(MAX_CONFIDENCE, avg + cluster_boost), 2)


class ConfidenceManager:
    """Manages confidence scores over time."""

    def __init__(self, decay_rate: float = 0.02):
        self.decay_rate = decay_rate
        self.corrections: dict[str, int] = {}
        self.last_used: dict[str, datetime] = {}

    def record_use(self, instinct_id: str):
        """Record that an instinct was used."""
        self.last_used[instinct_id] = datetime.utcnow()

    def record_correction(self, instinct_id: str):
        """Record that a user corrected an instinct."""
        self.corrections[instinct_id] = self.corrections.get(instinct_id, 0) + 1

    def get_adjusted_confidence(
        self,
        instinct_id: str,
        base_confidence: float
    ) -> float:
        """Get confidence adjusted for corrections and decay."""
        factors = ConfidenceFactors()

        # Apply correction penalty
        factors.user_corrections = self.corrections.get(instinct_id, 0)

        # Calculate decay
        if instinct_id in self.last_used:
            days_since = (datetime.utcnow() - self.last_used[instinct_id]).days
            factors.recency_boost = -calculate_decay(0, days_since, self.decay_rate)

        return calculate_confidence(factors)


if __name__ == '__main__':
    # Test confidence calculations
    print("Confidence Calculation Tests:")
    print()

    # Test occurrence-based confidence
    for count in [1, 3, 5, 10, 20]:
        base = calculate_base_confidence(count)
        print(f"  {count} occurrences → base confidence: {base}")

    print()

    # Test with corrections
    for corrections in [0, 1, 2, 3]:
        confidence = apply_corrections(0.7, corrections)
        print(f"  {corrections} corrections → confidence: {confidence}")

    print()

    # Test full calculation
    factors = ConfidenceFactors(
        occurrence_count=5,
        user_corrections=1,
        consistency_score=0.85
    )
    final = calculate_confidence(factors)
    print(f"  Final confidence: {final} ({get_confidence_level(final)})")
