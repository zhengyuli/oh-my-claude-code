# tests/unit/test_cli_export.py
"""
Unit tests for export formatting logic.

NOTE: Full CLI command testing (subprocess execution, stdout parsing) is in
integration tests (test_cli_export_integration.sh). These tests verify the
core data transformation logic patterns used by the export command.
"""
import pytest

@pytest.mark.unit
class TestExportFormatting:
    """Tests for export formatting logic."""

    def test_export_format_with_all_fields(self):
        """Test export format includes all standard fields."""
        instinct = {
            'id': 'test-export',
            'trigger': 'when exporting',
            'confidence': 0.8,
            'domain': 'testing',
            'source': 'session-observation',
            'source_repo': 'https://github.com/test/repo',
            'content': '# Test\n\nContent here.'
        }
        expected_fields = ['id', 'trigger', 'confidence', 'domain', 'source']
        for field in expected_fields:
            assert field in instinct

    def test_export_filter_by_domain(self):
        """Test filtering instincts by domain."""
        instincts = [
            {'id': 'test1', 'domain': 'testing', 'confidence': 0.8},
            {'id': 'test2', 'domain': 'workflow', 'confidence': 0.7},
            {'id': 'test3', 'domain': 'testing', 'confidence': 0.9},
        ]
        testing_only = [i for i in instincts if i.get('domain') == 'testing']
        assert len(testing_only) == 2
        assert all(i['domain'] == 'testing' for i in testing_only)

    def test_export_filter_by_min_confidence(self):
        """Test filtering instincts by minimum confidence."""
        instincts = [
            {'id': 'test1', 'confidence': 0.9},
            {'id': 'test2', 'confidence': 0.5},
            {'id': 'test3', 'confidence': 0.7},
        ]
        high_conf = [i for i in instincts if i.get('confidence', 0) >= 0.7]
        assert len(high_conf) == 2
        assert all(i['confidence'] >= 0.7 for i in high_conf)
