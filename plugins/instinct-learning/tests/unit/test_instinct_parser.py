"""
Instinct parser tests - optimized with parametrize.
"""

import pytest
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file


@pytest.mark.unit
class TestInstinctParser:
    """Tests for instinct file parsing."""

    def test_parse_single_instinct_all_fields(self):
        """Test parsing a single instinct with all standard fields."""
        content = '''---
id: test-instinct
trigger: "when testing code"
confidence: 0.85
domain: testing
source: session-observation
created: 2026-02-28T10:00:00Z
---
# Test Instinct

## Action
Run the tests first.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test-instinct'
        assert result[0]['trigger'] == 'when testing code'
        assert result[0]['confidence'] == 0.85
        assert result[0]['domain'] == 'testing'

    def test_parse_multiple_instincts(self):
        """Test parsing multiple instincts in one file."""
        content = '''---
id: first
confidence: 0.8
---
First

---
id: second
confidence: 0.7
---
Second'''
        result = parse_instinct_file(content)
        assert len(result) == 2
        assert result[0]['id'] == 'first'
        assert result[1]['id'] == 'second'

    def test_parse_duplicate_ids(self):
        """Test parsing multiple instincts with same ID."""
        content = '''---
id: duplicate
trigger: "first"
---
First

---
id: duplicate
trigger: "second"
---
Second'''
        result = parse_instinct_file(content)
        assert len(result) == 2
        assert all(i['id'] == 'duplicate' for i in result)

    @pytest.mark.parametrize("quote_type,expected", [
        ('double', 'quoted text'),
        ('single', 'single quoted'),
    ])
    def test_parse_with_quotes(self, quote_type, expected):
        """Test parsing values with different quote types."""
        if quote_type == 'double':
            content = '''---
id: test
trigger: "quoted text"
---
Content'''
        else:
            content = """---
id: test
trigger: 'single quoted'
---
Content"""
        result = parse_instinct_file(content)
        assert result[0]['trigger'] == expected

    @pytest.mark.parametrize("confidence,value", [
        (0.75, 0.75),
        (1, 1.0),
        (0.0, 0.0),
        (0.5, 0.5),
    ])
    def test_parse_confidence_values(self, confidence, value):
        """Test parsing various confidence values."""
        content = f'''---
id: test
confidence: {confidence}
---
Content'''
        result = parse_instinct_file(content)
        assert result[0]['confidence'] == value
        assert isinstance(result[0]['confidence'], float)

    def test_parse_without_id_is_skipped(self):
        """Test that instincts without ID are skipped."""
        content = '''---
trigger: "no id"
confidence: 0.5
---
Content'''
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_with_empty_content(self):
        """Test parsing instinct with empty content section."""
        content = '''---
id: test
trigger: "test"
---
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test'
        assert result[0].get('content') == ''

    def test_parse_multiline_content(self):
        """Test parsing multiline markdown content."""
        content = '''---
id: test
---
# Header

Paragraph one.

## Subsection

More content.
'''
        result = parse_instinct_file(content)
        assert 'Header' in result[0]['content']
        assert 'Paragraph one' in result[0]['content']

    def test_parse_content_with_code_blocks(self):
        """Test parsing content with markdown code blocks."""
        content = '''---
id: test
---
## Action

```python
def hello():
    print("world")
```
'''
        result = parse_instinct_file(content)
        assert 'def hello():' in result[0]['content']

    def test_parse_special_characters(self):
        """Test parsing values with special characters including unicode."""
        content = '''---
id: test
trigger: "when $VAR is set & <tag> 使用中文"
---
Content with emoji 🎉 and symbols €£¥
'''
        result = parse_instinct_file(content)
        assert '$VAR' in result[0]['trigger']
        assert '使用中文' in result[0]['trigger']
        assert '🎉' in result[0]['content']

    def test_parse_content_preserves_newlines(self):
        """Test that content preserves newline formatting."""
        content = '''---
id: test
---
Line one

Line two

Line three
'''
        result = parse_instinct_file(content)
        assert 'Line one' in result[0]['content']
        assert 'Line two' in result[0]['content']

    def test_parse_content_stripped(self):
        """Test that content is stripped of leading/trailing whitespace."""
        content = '''---
id: test
---


   Content with spaces

'''
        result = parse_instinct_file(content)
        assert result[0]['content'].startswith('Content')
        assert not result[0]['content'].startswith('   ')

    def test_parse_missing_optional_fields(self):
        """Test parsing with only required fields."""
        content = '''---
id: test
---
Content'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test'
        assert 'trigger' not in result[0]

    def test_parse_with_source_repo_field(self):
        """Test parsing source_repo field."""
        content = '''---
id: test
source_repo: https://github.com/example/repo
---
Content'''
        result = parse_instinct_file(content)
        assert result[0]['source_repo'] == 'https://github.com/example/repo'

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        result = parse_instinct_file('')
        assert len(result) == 0

    def test_parse_only_frontmatter_no_content(self):
        """Test parsing file with only frontmatter markers."""
        content = '''---
'''
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_malformed_frontmatter_skipped(self):
        """Test that malformed frontmatter is handled gracefully."""
        content = '''---
id: valid
trigger: "valid"
confidence: 0.8
---
Valid

---
id: malformed
trigger: "unclosed quote
confidence: 0.5
---
Malformed'''
        result = parse_instinct_file(content)
        assert len(result) >= 1
        assert any(i.get('id') == 'valid' for i in result)

    def test_parse_very_long_content(self):
        """Test parsing instinct with very long content."""
        long_content = "\n".join([f"Line {i}" for i in range(1000)])
        content = f'''---
id: test
---
{long_content}
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert 'Line 999' in result[0]['content']

    def test_parse_content_with_yaml_like_text(self):
        """Test content that looks like YAML but isn't frontmatter."""
        content = '''---
id: test
---
This content has YAML-like text:

key: value
nested:
  item: value

But it should be treated as content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert 'key: value' in result[0]['content']


@pytest.mark.unit
class TestSecurity:
    """Security tests for instinct parser."""

    def test_python_code_injection_blocked(self):
        """Python object injection in YAML should be blocked."""
        malicious = """---
id: test
trigger: !!python/object/apply:builtins.eval
  args: ['print("pwned")']
---
Content"""
        result = parse_instinct_file(malicious)
        assert len(result) == 0

    def test_confidence_range_validated(self):
        """Confidence must be 0.0-1.0, otherwise entry is skipped."""
        invalid = """---
id: test
confidence: 1.5
---
Content"""
        result = parse_instinct_file(invalid)
        assert len(result) == 0

    def test_unknown_keys_rejected(self):
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
