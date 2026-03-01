"""Security tests for instinct parser."""
import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file


def test_python_code_injection_blocked():
    """Python object injection in YAML should be blocked."""
    # Attempt to inject Python object via YAML
    malicious = """---
id: test
trigger: !!python/object/apply:builtins.eval
  args: ['print("pwned")']
---
Content here
"""
    result = parse_instinct_file(malicious)
    # yaml.safe_load() rejects Python object tags, so the entry is skipped
    # This is the correct secure behavior
    assert len(result) == 0
    # The important thing is no code was executed (no crash)


def test_confidence_range_validated():
    """Confidence must be 0.0-1.0, otherwise entry is skipped."""
    invalid = """---
id: test
confidence: 1.5
---
Content
"""
    result = parse_instinct_file(invalid)
    # Invalid confidence should cause the entry to be skipped
    assert len(result) == 0


def test_unknown_keys_rejected():
    """Unknown YAML keys should be filtered out."""
    with_unknown = """---
id: test
trigger: "when testing"
__dangerous_key__: "arbitrary code execution"
---
"""
    result = parse_instinct_file(with_unknown)
    assert len(result) == 1
    assert '__dangerous_key__' not in result[0]
