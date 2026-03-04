"""
CLI parser tests - optimized with fixtures and parametrize.
"""

import pytest
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file
from utils.file_io import load_all_instincts
import utils.file_io as file_io


@pytest.fixture
def temp_data_dir(tmp_path):
    """Setup temporary data directory."""
    data_dir = tmp_path / 'instincts'
    data_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def patch_directories(temp_data_dir):
    """Patch file_io directories to temp directory."""
    personal_dir = temp_data_dir / 'instincts' / 'personal'
    inherited_dir = temp_data_dir / 'instincts' / 'inherited'
    personal_dir.mkdir(parents=True, exist_ok=True)
    inherited_dir.mkdir(parents=True, exist_ok=True)

    original_personal = file_io.PERSONAL_DIR
    original_inherited = file_io.INHERITED_DIR

    file_io.PERSONAL_DIR = personal_dir
    file_io.INHERITED_DIR = inherited_dir

    yield personal_dir, inherited_dir

    file_io.PERSONAL_DIR = original_personal
    file_io.INHERITED_DIR = original_inherited


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

    def test_parse_multiple_instincts(self):
        """Test parsing multiple instincts in one file."""
        content = '''---
id: first
confidence: 0.7
---
Content one.

---
id: second
confidence: 0.8
---
Content two.
'''
        result = parse_instinct_file(content)
        assert len(result) == 2
        assert result[0]['id'] == 'first'
        assert result[1]['id'] == 'second'

    def test_parse_without_frontmatter_or_id(self):
        """Test that content without proper frontmatter or ID is ignored."""
        content = 'This is just content without frontmatter.'
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_instinct_missing_id(self):
        """Test that instincts without id are filtered out."""
        content = '''---
trigger: "no id"
confidence: 0.5
---
Content.'''
        result = parse_instinct_file(content)
        assert len(result) == 0

    def test_parse_empty_content(self):
        """Test parsing instinct with empty content."""
        content = '''---
id: empty
trigger: "test"
---
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['content'].strip() == ''


@pytest.mark.unit
class TestLoadAllInstincts:
    """Tests for load_all_instincts function."""

    @pytest.mark.parametrize("ext,file_id", [
        ('yaml', 'yaml-instinct'),
        ('yml', 'yml-instinct'),
        ('md', 'md-instinct'),
    ])
    def test_load_from_various_extensions(self, patch_directories, ext, file_id):
        """Test loading instincts from different file extensions."""
        content = f'''---
id: {file_id}
trigger: "trigger"
confidence: 0.8
---
Content.'''
        (patch_directories[0] / f'test.{ext}').write_text(content)

        result = load_all_instincts()
        assert len(result) == 1
        assert result[0]['id'] == file_id
        assert result[0]['_source_type'] == 'personal'

    def test_load_from_multiple_directories(self, patch_directories):
        """Test loading from both personal and inherited directories."""
        (patch_directories[0] / 'personal.yaml').write_text('---\nid: p\nconfidence: 0.7\n---\nP')
        (patch_directories[1] / 'inherited.yaml').write_text('---\nid: i\nconfidence: 0.8\n---\nI')

        result = load_all_instincts()
        assert len(result) == 2

        ids = [i['id'] for i in result]
        assert 'p' in ids
        assert 'i' in ids

        personal = next(i for i in result if i['id'] == 'p')
        inherited = next(i for i in result if i['id'] == 'i')
        assert personal['_source_type'] == 'personal'
        assert inherited['_source_type'] == 'inherited'

    def test_load_empty_directories(self, patch_directories):
        """Test loading from empty directories."""
        result = load_all_instincts()
        assert len(result) == 0

    def test_load_handles_invalid_files(self, patch_directories):
        """Test that invalid files don't crash the loader."""
        (patch_directories[0] / 'invalid.yaml').write_text('this is not valid yaml: [')
        (patch_directories[0] / 'valid.yaml').write_text('---\nid: valid\ntrigger: "test"\n---\nContent')

        result = load_all_instincts()
        assert len(result) == 1
        assert result[0]['id'] == 'valid'
