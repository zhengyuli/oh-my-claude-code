#!/usr/bin/env python3
"""
Clustering Library

Groups related instincts for evolution into capabilities.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
import sys
import os

# Add lib to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instinct_parser import Instinct
from confidence import calculate_cluster_confidence, AUTO_APPROVE_THRESHOLD


@dataclass
class Cluster:
    """Represents a cluster of related instincts."""
    domain: str
    instincts: list[Instinct]
    avg_confidence: float
    capability_type: str  # 'skill', 'command', or 'agent'

    @property
    def count(self) -> int:
        return len(self.instincts)

    def get_actions(self) -> list[str]:
        """Extract all actions from instincts."""
        return [i.action for i in self.instincts if i.action]

    def get_triggers(self) -> list[str]:
        """Extract all triggers from instincts."""
        return [i.trigger for i in self.instincts]


# Evolution thresholds
MIN_INSTINCTS_FOR_CLUSTER = 3
MIN_AVG_CONFIDENCE = 0.7


def group_by_domain(instincts: list[Instinct]) -> dict[str, list[Instinct]]:
    """Group instincts by domain."""
    grouped = defaultdict(list)
    for instinct in instincts:
        grouped[instinct.domain].append(instinct)
    return dict(grouped)


def determine_capability_type(instincts: list[Instinct]) -> str:
    """Determine the best capability type for a cluster."""
    # Analyze triggers to determine type
    triggers = [i.trigger.lower() for i in instincts]

    # Count trigger patterns
    auto_keywords = ['when', 'always', 'automatically', 'on']
    command_keywords = ['run', 'execute', 'perform', 'do']
    complex_keywords = ['analyze', 'research', 'investigate', 'design']

    auto_count = sum(1 for t in triggers if any(k in t for k in auto_keywords))
    command_count = sum(1 for t in triggers if any(k in t for k in command_keywords))
    complex_count = sum(1 for t in triggers if any(k in t for k in complex_keywords))

    # Determine type based on patterns
    if complex_count > len(instincts) * 0.3:
        return 'agent'  # Complex tasks need an agent
    elif command_count > len(instincts) * 0.3:
        return 'command'  # User-invoked tasks
    else:
        return 'skill'  # Default to auto-triggered skill


def create_clusters(
    instincts: list[Instinct],
    min_size: int = MIN_INSTINCTS_FOR_CLUSTER,
    min_confidence: float = MIN_AVG_CONFIDENCE
) -> list[Cluster]:
    """Create clusters from instincts."""
    clusters = []

    # Group by domain
    by_domain = group_by_domain(instincts)

    for domain, domain_instincts in by_domain.items():
        # Check minimum size
        if len(domain_instincts) < min_size:
            continue

        # Calculate average confidence
        confidences = [i.confidence for i in domain_instincts]
        avg_confidence = sum(confidences) / len(confidences)

        # Check minimum confidence
        if avg_confidence < min_confidence:
            continue

        # Determine capability type
        capability_type = determine_capability_type(domain_instincts)

        clusters.append(Cluster(
            domain=domain,
            instincts=domain_instincts,
            avg_confidence=round(avg_confidence, 2),
            capability_type=capability_type
        ))

    # Sort by average confidence (highest first)
    clusters.sort(key=lambda c: c.avg_confidence, reverse=True)

    return clusters


def merge_similar_clusters(clusters: list[Cluster]) -> list[Cluster]:
    """Merge clusters with similar domains."""
    # Simple implementation: keep clusters separate
    # Future: implement semantic similarity merging
    return clusters


def filter_ready_for_evolution(clusters: list[Cluster]) -> list[Cluster]:
    """Filter clusters that are ready for evolution."""
    return [
        c for c in clusters
        if c.count >= MIN_INSTINCTS_FOR_CLUSTER
        and c.avg_confidence >= AUTO_APPROVE_THRESHOLD
    ]


def generate_capability_name(cluster: Cluster) -> str:
    """Generate a name for the evolved capability."""
    # Use domain as base
    domain = cluster.domain.replace('-', ' ').title()

    # Add suffix based on type
    suffixes = {
        'skill': 'Workflow',
        'command': 'Task',
        'agent': 'Specialist'
    }

    suffix = suffixes.get(cluster.capability_type, 'Capability')
    return f"{domain} {suffix}"


def generate_capability_description(cluster: Cluster) -> str:
    """Generate a description for the evolved capability."""
    actions = cluster.get_actions()
    triggers = cluster.get_triggers()

    if actions:
        # Summarize main actions
        main_actions = actions[:3]
        action_text = ', '.join(main_actions[:2])
        if len(actions) > 2:
            action_text += f", and {len(actions) - 2} more behaviors"
        return f"Automated {cluster.domain} patterns: {action_text}"
    else:
        return f"Learned {cluster.domain} behaviors from {cluster.count} patterns"


class EvolutionEngine:
    """Manages the evolution of instincts into capabilities."""

    def __init__(self, min_cluster_size: int = MIN_INSTINCTS_FOR_CLUSTER):
        self.min_cluster_size = min_cluster_size
        self.clusters: list[Cluster] = []

    def analyze(self, instincts: list[Instinct]) -> list[Cluster]:
        """Analyze instincts and create clusters."""
        self.clusters = create_clusters(
            instincts,
            min_size=self.min_cluster_size
        )
        return self.clusters

    def get_ready_clusters(self) -> list[Cluster]:
        """Get clusters ready for evolution."""
        return filter_ready_for_evolution(self.clusters)

    def get_pending_clusters(self) -> list[Cluster]:
        """Get clusters that need more data."""
        return [
            c for c in self.clusters
            if c not in self.get_ready_clusters()
        ]

    def suggest_evolution(self, cluster: Cluster) -> dict:
        """Generate evolution suggestion for a cluster."""
        return {
            'name': generate_capability_name(cluster),
            'type': cluster.capability_type,
            'description': generate_capability_description(cluster),
            'domain': cluster.domain,
            'instinct_count': cluster.count,
            'avg_confidence': cluster.avg_confidence,
            'triggers': cluster.get_triggers(),
            'actions': cluster.get_actions()
        }


if __name__ == '__main__':
    # Test clustering with sample instincts
    from instinct_parser import Instinct
    from datetime import datetime

    test_instincts = [
        Instinct(
            id='test-first-approach',
            trigger='when implementing new features',
            confidence=0.8,
            domain='testing',
            created=datetime.utcnow().isoformat(),
            action='Write tests before implementation'
        ),
        Instinct(
            id='run-tests-after-edit',
            trigger='when editing source files',
            confidence=0.75,
            domain='testing',
            created=datetime.utcnow().isoformat(),
            action='Run related tests after changes'
        ),
        Instinct(
            id='mock-external-deps',
            trigger='when testing with APIs',
            confidence=0.7,
            domain='testing',
            created=datetime.utcnow().isoformat(),
            action='Mock external dependencies in tests'
        ),
        Instinct(
            id='commit-often',
            trigger='when making progress',
            confidence=0.6,
            domain='git',
            created=datetime.utcnow().isoformat(),
            action='Commit frequently with clear messages'
        )
    ]

    engine = EvolutionEngine()
    clusters = engine.analyze(test_instincts)

    print(f"Created {len(clusters)} clusters:")
    for cluster in clusters:
        print(f"\n  Domain: {cluster.domain}")
        print(f"  Type: {cluster.capability_type}")
        print(f"  Count: {cluster.count}")
        print(f"  Avg Confidence: {cluster.avg_confidence}")

        suggestion = engine.suggest_evolution(cluster)
        print(f"  Suggested Name: {suggestion['name']}")
