# tests/unit/test_cli_parser.py
import pytest
from instinct_cli import parse_instinct_file

@pytest.mark.unit
class TestParseInstinctFile:
    """Tests for parse_instinct_file function."""

    def test_parse_single_instinct(self):
        """Test parsing a single instinct with all fields."""
        content = '''---
id: test-instinct
trigger: "when testing code"
confidence: 0.85
domain: testing
source: session-observation
---
# Test Instinct

## Action
Run tests.
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
id: first-instinct
trigger: "trigger one"
confidence: 0.7
---
Content one.

---
id: second-instinct
trigger: "trigger two"
confidence: 0.8
---
Content two.
'''
        result = parse_instinct_file(content)
        assert len(result) == 2
        assert result[0]['id'] == 'first-instinct'
        assert result[1]['id'] == 'second-instinct'

    def test_parse_instinct_without_frontmatter_is_ignored(self):
        """Test that content without proper frontmatter is ignored."""
        content = 'This is just content without frontmatter.'
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_instinct_missing_id_is_filtered(self):
        """Test that instincts without id are filtered out."""
        content = '''---
trigger: "no id here"
confidence: 0.5
---
Some content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_instinct_default_confidence(self):
        """Test that missing confidence doesn't cause errors."""
        content = '''---
id: no-confidence
trigger: "testing"
---
Content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert 'confidence' not in result[0]

    def test_parse_instinct_quoted_values(self):
        """Test parsing values with different quote styles."""
        content = '''---
id: quoted-test
trigger: "double quoted"
domain: 'single quoted'
confidence: 0.9
---
Content.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['trigger'] == 'double quoted'
        assert result[0]['domain'] == 'single quoted'

    def test_parse_empty_content(self):
        """Test parsing instinct with empty content."""
        content = '''---
id: empty-content
trigger: "trigger"
---
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['content'].strip() == ''

    @pytest.mark.parametrize("content,expected_count", [
        ('---\nid: test\nconfidence: 0.5\n---\n', 1),
        ('---\nid: test\n---\n\n---\nid: test2\n---\n', 2),
        ('no frontmatter here', 0),
        ('', 0),
    ])
    def test_parse_various_formats(self, content, expected_count):
        """Test parsing various content formats."""
        result = parse_instinct_file(content)
        assert len(result) == expected_count
