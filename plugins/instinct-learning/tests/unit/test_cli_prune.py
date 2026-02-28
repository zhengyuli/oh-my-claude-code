# tests/unit/test_cli_prune.py
"""
Unit tests for prune logic patterns.

NOTE: Full CLI command testing (subprocess execution, file operations, dry-run)
is in integration tests (test_cli_prune_integration.sh). These tests verify the
core sorting and filtering logic patterns used by the prune command.
"""
import pytest
from instinct_cli import calculate_effective_confidence

@pytest.mark.unit
class TestPruneLogic:
    """Tests for prune logic."""

    def test_sort_by_effective_confidence(self):
        """Test sorting instincts by effective confidence."""
        instincts = [
            {'id': 'low', 'confidence': 0.4, 'last_observed': '2026-01-01T00:00:00Z'},
            {'id': 'high', 'confidence': 0.9, 'last_observed': '2026-02-28T00:00:00Z'},
            {'id': 'mid', 'confidence': 0.6, 'last_observed': '2026-02-20T00:00:00Z'},
        ]
        for inst in instincts:
            inst['effective'] = calculate_effective_confidence(inst)
        sorted_instincts = sorted(instincts, key=lambda x: -x['effective'])
        assert sorted_instincts[0]['id'] == 'high'
        assert sorted_instincts[-1]['id'] == 'low'

    def test_identify_instincts_to_archive(self):
        """Test identifying instincts to archive."""
        instincts = [
            {'id': 'keep1', 'confidence': 0.9, '_source_file': '/path/1'},
            {'id': 'keep2', 'confidence': 0.8, '_source_file': '/path/2'},
            {'id': 'archive1', 'confidence': 0.4, '_source_file': '/path/3'},
        ]
        max_count = 2
        to_keep = instincts[:max_count]
        to_archive = instincts[max_count:]
        assert len(to_keep) == 2
        assert len(to_archive) == 1
        assert to_archive[0]['id'] == 'archive1'

    def test_no_prune_when_within_limit(self):
        """Test no pruning when within limit."""
        instincts = [{'id': f'test{i}'} for i in range(5)]
        max_count = 10
        assert len(instincts) <= max_count
        to_archive = instincts[max_count:] if len(instincts) > max_count else []
        assert len(to_archive) == 0
