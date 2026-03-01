# tests/unit/test_cli_parser.py
import pytest
import sys
import os
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file
from utils.file_io import load_all_instincts
import shutil

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


@pytest.mark.unit
class TestLoadAllInstincts:
    """Tests for load_all_instincts function."""

    def test_load_from_yaml_file(self, temp_data_dir):
        """Test loading instincts from .yaml file."""
        yaml_content = '''---
id: yaml-instinct
trigger: "yaml trigger"
confidence: 0.75
domain: yaml-test
---
# YAML Instinct
Content here.
'''
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        (personal_dir / 'test.yaml').write_text(yaml_content)

        # Temporarily patch the directories
        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = temp_data_dir / 'instincts' / 'inherited'

        try:
            result = load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'yaml-instinct'
            assert result[0]['_source_type'] == 'personal'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_yml_file(self, temp_data_dir):
        """Test loading instincts from .yml file."""
        yml_content = '''---
id: yml-instinct
trigger: "yml trigger"
confidence: 0.8
---
Content.
'''
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        (personal_dir / 'test.yml').write_text(yml_content)

        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = temp_data_dir / 'instincts' / 'inherited'

        try:
            result = load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'yml-instinct'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_md_file(self, temp_data_dir):
        """Test loading instincts from .md file."""
        md_content = '''---
id: md-instinct
trigger: "md trigger"
confidence: 0.9
---
Content.
'''
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        (personal_dir / 'test.md').write_text(md_content)

        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = temp_data_dir / 'instincts' / 'inherited'

        try:
            result = load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'md-instinct'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_multiple_directories(self, temp_data_dir):
        """Test loading from both personal and inherited directories."""
        personal_content = '''---
id: personal-instinct
trigger: "personal"
confidence: 0.7
---
Personal content.
'''
        inherited_content = '''---
id: inherited-instinct
trigger: "inherited"
confidence: 0.8
---
Inherited content.
'''
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        inherited_dir = temp_data_dir / 'instincts' / 'inherited'
        (personal_dir / 'personal.yaml').write_text(personal_content)
        (inherited_dir / 'inherited.yaml').write_text(inherited_content)

        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = inherited_dir

        try:
            result = load_all_instincts()
            assert len(result) == 2

            ids = [i['id'] for i in result]
            assert 'personal-instinct' in ids
            assert 'inherited-instinct' in ids

            # Check source types
            personal = next(i for i in result if i['id'] == 'personal-instinct')
            inherited = next(i for i in result if i['id'] == 'inherited-instinct')
            assert personal['_source_type'] == 'personal'
            assert inherited['_source_type'] == 'inherited'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_empty_directories(self, temp_data_dir):
        """Test loading from empty directories."""
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        inherited_dir = temp_data_dir / 'instincts' / 'inherited'

        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = inherited_dir

        try:
            result = load_all_instincts()
            assert len(result) == 0
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_handles_invalid_files(self, temp_data_dir):
        """Test that invalid files don't crash the loader."""
        personal_dir = temp_data_dir / 'instincts' / 'personal'
        # Create an invalid file
        (personal_dir / 'invalid.yaml').write_text('this is not valid yaml: [')
        # Create a valid file
        valid_content = '''---
id: valid-instinct
trigger: "valid"
---
Content.
'''
        (personal_dir / 'valid.yaml').write_text(valid_content)

        import utils.file_io as file_io
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = temp_data_dir / 'instincts' / 'inherited'

        try:
            # Should not crash, should load only valid file
            result = load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'valid-instinct'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited
