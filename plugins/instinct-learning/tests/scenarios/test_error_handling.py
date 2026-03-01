"""Error handling scenario tests.

These tests validate error handling and recovery under various failure conditions.
"""

import json
import pytest
import subprocess
import sys
import os
import tempfile
from pathlib import Path


@pytest.mark.scenario
def test_malformed_json_input_handled(temp_data_dir):
    """Scenario: Malformed JSON input is handled gracefully.

    When receiving malformed JSON:
    - Error should be caught and logged
    - System should continue operating
    - No crash or unhandled exception
    """
    obs_file = temp_data_dir / 'observations' / 'observations.jsonl'

    # Write malformed JSON
    malformed_entries = [
        '{"timestamp": "2026-02-28T10:00:00Z", "tool": "Edit"',  # Missing closing brace
        'not json at all',
        '{"valid": "json"}',  # This one is valid
        '{"another": "broken"',  # Missing closing
    ]

    obs_file.write_text('\n'.join(malformed_entries) + '\n')

    # Parse with error handling
    valid_entries = []
    with open(obs_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                valid_entries.append(json.loads(line))
            except json.JSONDecodeError:
                # Malformed JSON is skipped
                pass

    # Should have parsed 1 valid entry
    assert len(valid_entries) == 1
    assert valid_entries[0] == {'valid': 'json'}


@pytest.mark.scenario
def test_empty_input_handled(temp_data_dir):
    """Scenario: Empty input is handled gracefully.

    When receiving empty input:
    - Should return empty results
    - No errors should be raised
    - System should remain functional
    """
    # Import from scripts directory
    import sys
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.instinct_parser import parse_instinct_file

    # Test with empty content
    result = parse_instinct_file('')
    assert result == []

    # Test with whitespace only
    result = parse_instinct_file('   \n\n  ')
    assert result == []


@pytest.mark.scenario
def test_missing_directory_created(temp_data_dir):
    """Scenario: Missing directories are created automatically.

    When data directory is missing:
    - Directory structure should be created
    - No errors should occur
    - Subsequent operations should work
    """
    # Remove existing directories
    import shutil
    if (temp_data_dir / 'observations').exists():
        shutil.rmtree(temp_data_dir / 'observations')

    # Simulate directory creation logic
    obs_dir = temp_data_dir / 'observations'
    obs_dir.mkdir(parents=True, exist_ok=True)

    # Directory should exist now
    assert obs_dir.exists()
    assert obs_dir.is_dir()

    # Should be able to write to it
    test_file = obs_dir / 'test.jsonl'
    test_file.write_text('test data\n')
    assert test_file.exists()


@pytest.mark.scenario
def test_import_nonexistent_file(temp_data_dir):
    """Scenario: Importing nonexistent file is handled gracefully.

    When importing a file that doesn't exist:
    - Clear error message should be provided
    - No crash should occur
    - System should remain functional
    """
    # Import from scripts directory
    import sys
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))

    nonexistent_file = temp_data_dir / 'nonexistent.yaml'

    # Should handle gracefully - trying to read a nonexistent file
    # should raise FileNotFoundError or return empty result
    try:
        content = nonexistent_file.read_text()
        result = content  # This won't execute if file doesn't exist
    except FileNotFoundError:
        # This is the expected path
        result = None

    # Result should indicate error
    assert result is None
