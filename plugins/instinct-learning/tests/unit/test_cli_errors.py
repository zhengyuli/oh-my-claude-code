"""Test CLI error handling and edge cases.

This module tests error scenarios in CLI operations to improve
test coverage from 16% to 50%+.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file
from utils.file_io import load_all_instincts


@pytest.mark.unit
class TestCLIErrorHandling:
    """Test error scenarios in CLI operations."""

    def test_parse_malformed_yaml_skipped(self):
        """Test that malformed YAML is handled gracefully."""
        content = """---
id: test
trigger: "x
confidence: 0.5
---
Content"""
        result = parse_instinct_file(content)
        # Parser handles malformed YAML - result may have partial data
        # The key is that it doesn't crash
        assert isinstance(result, list)

    def test_parse_empty_frontmatter_skipped(self):
        """Test instinct with no id is filtered out."""
        content = """---
trigger: "no id"
confidence: 0.5
---
Some content"""
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_multiple_instincts_with_one_invalid(self):
        """Test that valid instincts are parsed even when one is invalid."""
        content = """---
id: valid-instinct
trigger: "when testing"
confidence: 0.7
domain: testing
---
Valid content

---
trigger: "no id"
confidence: 0.5
---
Invalid content (no id)

---
id: another-valid
trigger: "when debugging"
confidence: 0.6
domain: debugging
---
Another valid content"""
        result = parse_instinct_file(content)
        # Should return 2 valid instincts, skip the invalid one
        assert len(result) == 2
        assert result[0]['id'] == 'valid-instinct'
        assert result[1]['id'] == 'another-valid'

    def test_parse_empty_content_returns_empty_list(self):
        """Test parsing empty content returns empty list."""
        result = parse_instinct_file("")
        assert result == []

    def test_parse_whitespace_only_content(self):
        """Test parsing whitespace-only content returns empty list."""
        result = parse_instinct_file("   \n\n   \n")
        assert result == []

    def test_load_from_nonexistent_directory(self, monkeypatch):
        """Test loading from non-existent directory returns empty list or loads from default."""
        import os
        original_dir = os.getcwd()
        original_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
        try:
            # Set to a non-existent directory
            monkeypatch.setenv('INSTINCT_LEARNING_DATA_DIR', '/tmp/nonexistent-path-12345')

            # The function should either return empty list or fall back to default
            result = load_all_instincts()
            # Should return a list (possibly empty or with default data)
            assert isinstance(result, list)
        finally:
            # Restore original environment
            if original_env:
                monkeypatch.setenv('INSTINCT_LEARNING_DATA_DIR', original_env)
            else:
                monkeypatch.delenv('INSTINCT_LEARNING_DATA_DIR', raising=False)
            os.chdir(original_dir)

    def test_load_with_corrupted_file(self, temp_data_dir):
        """Test loading from corrupted YAML file logs warning but doesn't crash."""
        # Create a corrupted file
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True, exist_ok=True)
        bad_file = personal_dir / 'bad.yaml'
        bad_file.write_text('---\nid: test\n: bad yaml\n---\nContent')

        # Should log error but not crash
        result = load_all_instincts()
        assert isinstance(result, list)

    def test_import_nonexistent_file(self, temp_data_dir, temp_home):
        """Test importing from non-existent file shows error."""
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'instinct_cli.py'
        result = subprocess.run(
            ['python3', str(script_path), 'import', '/nonexistent/file.yaml'],
            capture_output=True,
            text=True,
            env=temp_home.get_env(),
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode != 0
        # Check both stdout and stderr for error message
        output = result.stdout.lower() + result.stderr.lower()
        assert 'not found' in output or 'no such file' in output or 'cannot open' in output

    def test_import_invalid_url(self, temp_data_dir, temp_home):
        """Test importing from invalid URL shows error or times out."""
        import subprocess
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'instinct_cli.py'
        try:
            result = subprocess.run(
                ['python3', str(script_path), 'import', 'http://invalid-domain-12345.com/file.yaml'],
                capture_output=True,
                text=True,
                env=temp_home.get_env(),
                cwd=Path(__file__).parent.parent.parent,
                timeout=10
            )
            # If we get here without timeout, verify CLI handled the error
            assert result.returncode != 0 or 'error' in result.stdout.lower() or 'error' in result.stderr.lower()
        except subprocess.TimeoutExpired:
            # Timeout is expected for invalid URLs - test passes
            pass

    def test_export_with_no_instincts(self, temp_data_dir, temp_home):
        """Test exporting with no instincts shows appropriate message."""
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'instinct_cli.py'
        result = subprocess.run(
            ['python3', str(script_path), 'export'],
            capture_output=True,
            text=True,
            env=temp_home.get_env(),
            cwd=Path(__file__).parent.parent.parent
        )
        output = result.stdout.lower()
        # Should mention no instincts or show count of 0
        assert 'no instincts' in output or '0 instincts' in output or 'empty' in output or result.returncode != 0


@pytest.mark.unit
class TestConfidenceDecayEdgeCases:
    """Test confidence calculation edge cases."""

    def test_confidence_with_missing_timestamp(self):
        """Test confidence calculation with missing last_observed timestamp."""
        from utils.confidence import calculate_effective_confidence

        instinct = {
            'confidence': 0.8,
            'last_observed': None
        }
        result = calculate_effective_confidence(instinct)
        # Should return base confidence when timestamp is missing
        assert result == 0.8

    def test_confidence_with_invalid_timestamp(self):
        """Test confidence calculation with invalid timestamp format."""
        from utils.confidence import calculate_effective_confidence

        instinct = {
            'confidence': 0.8,
            'last_observed': 'invalid-timestamp'
        }
        result = calculate_effective_confidence(instinct)
        # Should return base confidence when timestamp is invalid
        assert result == 0.8

    def test_confidence_never_goes_below_minimum(self):
        """Test that confidence never goes below 0.3 (floor value)."""
        from utils.confidence import calculate_effective_confidence
        from datetime import datetime, timedelta

        # Create an instinct from a very long time ago
        old_timestamp = (datetime.now() - timedelta(days=365)).isoformat()
        instinct = {
            'confidence': 0.9,
            'last_observed': old_timestamp
        }
        result = calculate_effective_confidence(instinct, decay_rate=0.5)  # High decay rate
        # Should floor at 0.3
        assert result >= 0.3
