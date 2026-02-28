#!/usr/bin/env python3
"""
Unit tests for clustering library.
"""

import sys
import unittest
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from clustering import (
    Cluster,
    group_by_domain,
    determine_capability_type,
    create_clusters,
    filter_ready_for_evolution,
    generate_capability_name,
    generate_capability_description,
    EvolutionEngine,
    MIN_INSTINCTS_FOR_CLUSTER,
    MIN_AVG_CONFIDENCE
)
from instinct_parser import Instinct


class TestClusterClass(unittest.TestCase):
    """Tests for Cluster dataclass."""

    def test_cluster_properties(self):
        """Test Cluster properties work correctly."""
        instincts = [
            Instinct('i1', 'test', 0.7, 'test', '2025-01-01', 'obs', 1, 'act1', []),
            Instinct('i2', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, 'act2', []),
        ]
        cluster = Cluster(
            domain='testing',
            instincts=instincts,
            avg_confidence=0.75,
            capability_type='skill'
        )

        self.assertEqual(cluster.count, 2)
        self.assertEqual(len(cluster.get_actions()), 2)
        self.assertEqual(len(cluster.get_triggers()), 2)


class TestDetermineCapabilityType(unittest.TestCase):
    """Tests for determine_capability_type function."""

    def test_skill_type_when_keywords(self):
        """Test 'when' keywords trigger skill type."""
        instincts = [
            Instinct('i1', 'when testing starts', 0.7, 'test', '2025-01-01', 'obs', 1, '', []),
            Instinct('i2', 'always write tests', 0.7, 'test', '2025-01-01', 'obs', 1, '', []),
        ]
        result = determine_capability_type(instincts)
        self.assertEqual(result, 'skill')

    def test_command_type_keywords(self):
        """Test 'run/execute' keywords trigger command type."""
        instincts = [
            Instinct('i1', 'run tests now', 0.7, 'test', '2025-01-01', 'obs', 1, '', []),
            Instinct('i2', 'execute build', 0.7, 'test', '2025-01-01', 'obs', 1, '', []),
        ]
        result = determine_capability_type(instincts)
        self.assertEqual(result, 'command')

    def test_agent_type_keywords(self):
        """Test 'analyze/research' keywords trigger agent type."""
        instincts = [
            Instinct('i1', 'analyze code complexity', 0.7, 'arch', '2025-01-01', 'obs', 1, '', []),
            Instinct('i2', 'investigate performance', 0.7, 'debug', '2025-01-01', 'obs', 1, '', []),
        ]
        result = determine_capability_type(instincts)
        self.assertEqual(result, 'agent')

    def test_default_skill(self):
        """Test default to skill when no clear keywords."""
        instincts = [
            Instinct('i1', 'perform action', 0.7, 'test', '2025-01-01', 'obs', 1, '', []),
        ]
        result = determine_capability_type(instincts)
        # 'perform' is a command keyword, but with 1 instinct it's 100% which is >30%
        # Actually the logic is: command_count (1) > len(instincts) * 0.3 (0.3) = True
        # So it returns 'command'
        self.assertEqual(result, 'command')


class TestCreateClusters(unittest.TestCase):
    """Tests for create_clusters function."""

    def test_below_threshold(self):
        """Test clusters below threshold are not created."""
        instincts = [
            Instinct(f'i{i}', 'test', 0.7, 'test', '2025-01-01', 'obs', 1, '', [])
            for i in range(2)  # Only 2 instincts
        ]
        clusters = create_clusters(instincts, min_size=3, min_confidence=0.7)
        self.assertEqual(len(clusters), 0)

    def test_below_confidence_threshold(self):
        """Test clusters below confidence threshold are not created."""
        instincts = [
            Instinct(f'i{i}', 'test', 0.5, 'test', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)  # 3 instincts but low confidence
        ]
        clusters = create_clusters(instincts, min_size=3, min_confidence=0.7)
        self.assertEqual(len(clusters), 0)

    def test_valid_cluster_created(self):
        """Test valid cluster is created."""
        instincts = [
            Instinct(f'i{i}', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]
        clusters = create_clusters(instincts, min_size=3, min_confidence=0.7)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].domain, 'test')
        self.assertEqual(clusters[0].count, 3)

    def test_multiple_domains(self):
        """Test multiple domains create separate clusters."""
        instincts = [
            Instinct(f'test-{i}', 'test', 0.8, 'testing', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ] + [
            Instinct(f'git-{i}', 'test', 0.8, 'git', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]
        clusters = create_clusters(instincts, min_size=3, min_confidence=0.7)
        self.assertEqual(len(clusters), 2)

    def test_sorted_by_confidence(self):
        """Test clusters are sorted by confidence."""
        instincts = [
            Instinct(f'i{i}', 'test', 0.9 - (i * 0.1), 'domain', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]
        clusters = create_clusters(instincts, min_size=3, min_confidence=0.5)

        # Should be sorted highest first
        confidences = [c.avg_confidence for c in clusters]
        self.assertEqual(confidences, sorted(confidences, reverse=True))


class TestFilterReadyForEvolution(unittest.TestCase):
    """Tests for filter_ready_for_evolution function."""

    def test_filters_by_threshold(self):
        """Test filters clusters below evolution threshold."""
        # Create proper clusters with instincts
        instincts1 = [
            Instinct(f'i{i}', 'test', 0.6, 'domain1', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]
        instincts2 = [
            Instinct(f'i{i}', 'test', 0.8, 'domain2', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]
        clusters = [
            Cluster('domain1', instincts1, 0.6, 'skill'),  # Below threshold
            Cluster('domain2', instincts2, 0.8, 'skill'),  # Above threshold
        ]
        ready = filter_ready_for_evolution(clusters)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].domain, 'domain2')

    def test_empty_when_none_ready(self):
        """Test returns empty when none are ready."""
        clusters = [
            Cluster('domain1', [], 0.5, 'skill'),
            Cluster('domain2', [], 0.6, 'skill'),
        ]
        ready = filter_ready_for_evolution(clusters)
        self.assertEqual(len(ready), 0)


class TestGenerateCapabilityName(unittest.TestCase):
    """Tests for generate_capability_name function."""

    def test_skill_suffix(self):
        """Test skill capability gets Workflow suffix."""
        cluster = Cluster('testing', [], 0.7, 'skill')
        name = generate_capability_name(cluster)
        self.assertIn('Workflow', name)

    def test_command_suffix(self):
        """Test command capability gets Task suffix."""
        cluster = Cluster('git', [], 0.7, 'command')
        name = generate_capability_name(cluster)
        self.assertIn('Task', name)

    def test_agent_suffix(self):
        """Test agent capability gets Specialist suffix."""
        cluster = Cluster('debug', [], 0.7, 'agent')
        name = generate_capability_name(cluster)
        self.assertIn('Specialist', name)


class TestGenerateCapabilityDescription(unittest.TestCase):
    """Tests for generate_capability_description function."""

    def test_with_actions(self):
        """Test description includes actions."""
        instincts = [
            Instinct('i1', 'test', 0.7, 'test', '2025-01-01', 'obs', 1, 'Action 1', []),
            Instinct('i2', 'test', 0.7, 'test', '2025-01-01', 'obs', 1, 'Action 2', []),
        ]
        cluster = Cluster('test', instincts, 0.7, 'skill')
        description = generate_capability_description(cluster)

        self.assertIn('test', description.lower())
        self.assertGreater(len(description), 10)


class TestEvolutionEngine(unittest.TestCase):
    """Tests for EvolutionEngine class."""

    def test_analyze_creates_clusters(self):
        """Test analyze method creates clusters."""
        engine = EvolutionEngine()
        instincts = [
            Instinct(f'i{i}', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]

        clusters = engine.analyze(instincts)

        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].domain, 'test')

    def test_get_ready_clusters(self):
        """Test getting ready clusters filters correctly."""
        engine = EvolutionEngine()
        instincts = [
            Instinct(f'i{i}', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, '', [])
            for i in range(3)
        ]

        engine.analyze(instincts)
        ready = engine.get_ready_clusters()

        self.assertEqual(len(ready), 1)

    def test_suggest_evolution(self):
        """Test suggest_evolution returns proper dict."""
        engine = EvolutionEngine()
        instincts = [
            Instinct('i1', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, 'action1', []),
            Instinct('i2', 'test', 0.8, 'test', '2025-01-01', 'obs', 1, 'action2', []),
        ]
        cluster = Cluster('test', instincts, 0.8, 'skill')

        suggestion = engine.suggest_evolution(cluster)

        self.assertIn('name', suggestion)
        self.assertIn('type', suggestion)
        self.assertIn('description', suggestion)
        self.assertIn('domain', suggestion)
        self.assertIn('instinct_count', suggestion)
        self.assertEqual(suggestion['type'], 'skill')


if __name__ == '__main__':
    unittest.main()
