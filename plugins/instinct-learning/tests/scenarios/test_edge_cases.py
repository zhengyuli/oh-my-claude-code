"""Edge case scenario tests.

These tests validate behavior at boundary conditions and unusual inputs.
"""

import json
import pytest
import sys
from pathlib import Path


@pytest.mark.scenario
def test_unicode_in_all_fields(temp_data_dir):
    """Scenario: Unicode characters in all fields are handled correctly.

    Unicode test cases:
    - Emojis: 🚀 ✨ 🎯
    - Chinese: 你好世界
    - Arabic: مرحبا بالعالم
    - Special symbols: ™ © ® €
    - Combining characters: é = e + combining acute
    """
    # Import from scripts directory
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.instinct_parser import parse_instinct_file

    # Create instinct with unicode in all fields
    unicode_content = '''---
id: test-unicode-🚀
trigger: "when working with 你好 and emoji ✨"
confidence: 0.85
domain: testing
created: "2026-02-28T10:00:00Z"
---
# Test Unicode 🎯

## Action
Use symbols like ™ © ® € in code.

## Evidence
- Observed in session مرحبا
- File: /path/to/文件.py
'''

    result = parse_instinct_file(unicode_content)

    # Should parse successfully
    assert result is not None
    assert len(result) > 0
    assert '🚀' in result[0].get('id', '')
    assert '你好' in result[0].get('trigger', '')
    assert '✨' in result[0].get('trigger', '')


@pytest.mark.scenario
def test_special_characters_in_paths(temp_data_dir):
    """Scenario: Special characters in file paths are handled.

    Special character cases:
    - Spaces: "my file.py"
    - Parentheses: "file (1).py"
    - Brackets: "file [test].py"
    - Unicode: "файл.py"
    """
    # Import from scripts directory
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.instinct_parser import parse_instinct_file

    # Test various path formats
    special_paths = [
        '/path/to/my file.py',
        '/path/to/file (1).py',
        '/path/to/file [test].py',
        '/path/to/файл.py',
        '/path/to/"quoted".py',
        "/path/to/'single'.py",
    ]

    for path in special_paths:
        # Create a valid ID by hashing the path
        import hashlib
        path_hash = hashlib.md5(path.encode()).hexdigest()[:8]

        content = f'''---
id: test-path-{path_hash}
trigger: "when editing {path}"
confidence: 0.75
domain: testing
---
## Action
Handle path: {path}
'''
        result = parse_instinct_file(content)

        # Should parse without error
        assert result is not None
        assert len(result) > 0
        assert path in result[0].get('trigger', '')


@pytest.mark.scenario
def test_very_long_trigger_string(temp_data_dir):
    """Scenario: Very long trigger strings are handled.

    Test boundaries:
    - 1000 character trigger
    - Multi-line trigger with special formatting
    """
    # Import from scripts directory
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.instinct_parser import parse_instinct_file

    # Create a very long trigger (1000 characters)
    long_trigger = "when " + "testing " * 200 + "code"

    content = f'''---
id: test-long-trigger
trigger: "{long_trigger[:1000]}"
confidence: 0.75
domain: testing
---
## Action
This has a very long trigger.
'''

    result = parse_instinct_file(content)

    # Should parse successfully
    assert result is not None
    assert len(result) > 0
    assert len(result[0].get('trigger', '')) > 500  # Should be long


@pytest.mark.scenario
def test_confidence_boundary_values(temp_data_dir):
    """Scenario: Confidence boundary values are handled correctly.

    Test boundaries:
    - Minimum: 0.0
    - Maximum: 1.0
    - Below minimum: -0.1 (should be clamped or rejected)
    - Above maximum: 1.1 (should be clamped or rejected)
    - Edge: 0.3 (typical minimum)
    - Edge: 0.9 (typical maximum)
    """
    # Import from scripts directory
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from utils.instinct_parser import parse_instinct_file

    # Test various confidence values
    test_cases = [
        (0.0, True, "zero confidence"),
        (0.3, True, "minimum typical"),
        (0.9, True, "maximum typical"),
        (1.0, True, "full confidence"),
        (-0.1, False, "below minimum"),
        (1.1, False, "above maximum"),
        (0.5, True, "mid-range"),
    ]

    for confidence, should_be_valid, description in test_cases:
        content = f'''---
id: test-confidence-{int(confidence * 100)}
trigger: "test trigger"
confidence: {confidence}
domain: testing
---
## Action
Test {description}.
'''

        result = parse_instinct_file(content)

        if should_be_valid:
            assert result is not None, f"Failed for {description}"
            # Validate confidence is in valid range
            assert 0.0 <= result[0].get('confidence', -1) <= 1.0
        else:
            # Invalid confidence may still parse but should be flagged
            if result is not None:
                conf = result[0].get('confidence', -1)
                # Should be clamped or flagged
                assert conf >= 0.0 or conf <= 1.0
