"""
Comprehensive instinct parser tests.

This module provides detailed testing of the YAML frontmatter parser
to achieve high coverage for the instinct_parser module.
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file


@pytest.mark.unit
class TestInstinctParser:
    """Comprehensive tests for instinct file parsing."""

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
        assert result[0]['source'] == 'session-observation'

    def test_parse_multiple_instincts(self):
        """Test parsing multiple instincts in one file."""
        content = '''---
id: first
trigger: "first trigger"
confidence: 0.8
---
# First

Content here.

---
id: second
trigger: "second trigger"
confidence: 0.7
---
# Second

More content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 2
        assert result[0]['id'] == 'first'
        assert result[1]['id'] == 'second'

    def test_parse_without_id_is_skipped(self):
        """Test that instincts without ID are skipped."""
        content = '''---
trigger: "no id"
confidence: 0.5
---
Content
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
Valid content.

---
id: malformed
trigger: "unclosed quote
confidence: 0.5
---
Malformed content
'''
        result = parse_instinct_file(content)
        # Should return the valid one, skip or handle malformed gracefully
        assert len(result) >= 1
        assert any(i.get('id') == 'valid' for i in result)

    def test_parse_confidence_as_float(self):
        """Test that confidence is parsed as float."""
        content = '''---
id: test
confidence: 0.75
---
Content
'''
        result = parse_instinct_file(content)
        assert result[0]['confidence'] == 0.75
        assert isinstance(result[0]['confidence'], float)

    def test_parse_confidence_integer(self):
        """Test parsing integer confidence values."""
        content = '''---
id: test
confidence: 1
---
Content
'''
        result = parse_instinct_file(content)
        assert result[0]['confidence'] == 1.0
        assert isinstance(result[0]['confidence'], float)

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
trigger: "test"
---
# Header

Paragraph one.

Paragraph two.

## Subsection

More content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert 'Header' in result[0]['content']
        assert 'Paragraph one' in result[0]['content']

    def test_parse_with_quotes_in_values(self):
        """Test parsing values with quotes - quotes are preserved in value."""
        content = '''---
id: test
trigger: "quoted text"
---
Content
'''
        result = parse_instinct_file(content)
        # Quotes in YAML are stripped during parsing
        assert result[0]['trigger'] == 'quoted text'

    def test_parse_with_single_quotes(self):
        """Test parsing values with single quotes."""
        content = """---
id: test
trigger: 'single quoted'
---
Content
"""
        result = parse_instinct_file(content)
        assert result[0]['trigger'] == 'single quoted'

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

    def test_parse_with_colon_in_trigger(self):
        """Test parsing trigger containing colon."""
        content = '''---
id: test
trigger: "when: error occurs"
---
Content
'''
        result = parse_instinct_file(content)
        # First colon after 'trigger' is the delimiter
        # The rest should be captured as value
        assert 'error occurs' in result[0]['trigger']

    def test_parse_special_characters_in_values(self):
        """Test parsing values with special characters."""
        content = '''---
id: test
trigger: "when $VAR is set & <tag> used"
---
Content
'''
        result = parse_instinct_file(content)
        assert '$VAR' in result[0]['trigger']

    def test_parse_content_preserves_newlines(self):
        """Test that content preserves newline formatting."""
        content = '''---
id: test
---
Line one

Line two


Line three (with blank line above)
'''
        result = parse_instinct_file(content)
        assert 'Line one' in result[0]['content']
        assert 'Line two' in result[0]['content']

    def test_parse_no_ending_delimiter(self):
        """Test parsing file without ending delimiter."""
        content = '''---
id: test
trigger: "test"
---
Content here
(no ending delimiter)
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test'

    def test_parse_whitespace_only_lines(self):
        """Test parsing with whitespace-only lines."""
        content = '''---


id: test


trigger: "test"


---


Content


'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test'

    def test_parse_unicode_characters(self):
        """Test parsing with unicode characters."""
        content = '''---
id: test
trigger: "when 使用中文"
---
Content with emoji 🎉 and symbols €£¥
'''
        result = parse_instinct_file(content)
        assert '使用中文' in result[0]['trigger']
        assert '🎉' in result[0]['content']

    def test_parse_missing_optional_fields(self):
        """Test parsing with only required fields."""
        content = '''---
id: test
---
Content
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'test'
        assert 'trigger' not in result[0]  # Optional field missing

    def test_parse_with_source_repo_field(self):
        """Test parsing source_repo field."""
        content = '''---
id: test
source_repo: https://github.com/example/repo
---
Content
'''
        result = parse_instinct_file(content)
        assert result[0]['source_repo'] == 'https://github.com/example/repo'

    def test_parse_confidence_zero(self):
        """Test parsing zero confidence."""
        content = '''---
id: test
confidence: 0.0
---
Content
'''
        result = parse_instinct_file(content)
        assert result[0]['confidence'] == 0.0

    def test_parse_confidence_boundary_values(self):
        """Test parsing confidence at boundary values."""
        for conf in [0.0, 0.3, 0.5, 0.7, 1.0]:
            content = f'''---
id: test
confidence: {conf}
---
Content
'''
            result = parse_instinct_file(content)
            assert result[0]['confidence'] == conf

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
        assert 'print("world")' in result[0]['content']

    def test_parse_content_with_yaml_like_content(self):
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

    def test_parse_duplicate_ids(self):
        """Test parsing multiple instincts with same ID."""
        content = '''---
id: duplicate
trigger: "first"
---
Content one

---
id: duplicate
trigger: "second"
---
Content two
'''
        result = parse_instinct_file(content)
        # Both should be included (filtering is caller's responsibility)
        assert len(result) == 2
        assert all(i['id'] == 'duplicate' for i in result)

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
