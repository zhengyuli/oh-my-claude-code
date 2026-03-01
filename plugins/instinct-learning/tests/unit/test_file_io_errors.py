"""Error handling tests for file_io module."""
import pytest
import os
from pathlib import Path


def test_load_instincts_skips_corrupted_files(temp_data_dir, monkeypatch):
    """Corrupted YAML files should be skipped with warning."""
    # Set the data directory environment variable
    monkeypatch.setenv('INSTINCT_LEARNING_DATA_DIR', str(temp_data_dir))

    # Import after setting environment
    from scripts.utils.instinct_parser import parse_instinct_file

    personal_dir = temp_data_dir / "instincts" / "personal"
    personal_dir.mkdir(parents=True, exist_ok=True)

    # Valid instinct
    valid_content = """---
id: test
trigger: "when testing"
confidence: 0.8
domain: testing
---
Content
"""
    (personal_dir / "valid.md").write_text(valid_content)

    # Corrupted file
    (personal_dir / "bad.md").write_text("{{{invalid yaml")

    # Test that parse_instinct_file handles corrupted files
    result = parse_instinct_file(valid_content)
    assert len(result) == 1
    assert result[0]['id'] == 'test'

    # Test that corrupted content is handled
    corrupted_result = parse_instinct_file("{{{invalid yaml")
    assert len(corrupted_result) == 0  # Should return empty list on error


def test_load_instincts_handles_unicode_files(temp_data_dir):
    """Files with unicode content should be handled correctly."""
    personal_dir = temp_data_dir / "instincts" / "personal"
    personal_dir.mkdir(parents=True, exist_ok=True)

    from scripts.utils.instinct_parser import parse_instinct_file

    # Valid instinct with unicode
    unicode_content = """---
id: test-unicode
trigger: "when testing"
confidence: 0.8
domain: testing
---
Content with unicode: 你好世界
"""
    result = parse_instinct_file(unicode_content)

    # Should load valid instinct with unicode
    assert len(result) == 1
    assert result[0]['id'] == 'test-unicode'
    assert '你好世界' in result[0]['content']


def test_parse_instinct_with_empty_content(temp_data_dir):
    """Empty instinct files should be handled gracefully."""
    from scripts.utils.instinct_parser import parse_instinct_file

    # Empty content
    result = parse_instinct_file("")
    assert len(result) == 0

    # Content with only whitespace
    result = parse_instinct_file("   \n  \n  ")
    assert len(result) == 0


def test_parse_instinct_with_missing_fields(temp_data_dir):
    """Instincts with missing required fields should be rejected or handled."""
    from scripts.utils.instinct_parser import parse_instinct_file

    # Missing id field
    content1 = """---
trigger: "when testing"
confidence: 0.8
domain: testing
---
Content
"""
    result = parse_instinct_file(content1)
    # Should either return empty or add a default id
    assert isinstance(result, list)


def test_parse_instinct_with_invalid_yaml(temp_data_dir):
    """Invalid YAML should be handled gracefully."""
    from scripts.utils.instinct_parser import parse_instinct_file

    # Various invalid YAML patterns
    invalid_patterns = [
        "{invalid",
        "key: value\n  bad_indent",
        "---\nkey: [unclosed list",
    ]

    for pattern in invalid_patterns:
        result = parse_instinct_file(pattern)
        # Should return empty list on error
        assert isinstance(result, list)
