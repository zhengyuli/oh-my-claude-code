"""
File I/O tests - optimized with fixtures and parametrize.
"""

import pytest
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils import file_io


@pytest.fixture
def mock_directories(tmp_path):
    """Setup mock directories, auto cleanup."""
    personal_dir = tmp_path / 'instincts' / 'personal'
    inherited_dir = tmp_path / 'instincts' / 'inherited'
    personal_dir.mkdir(parents=True)
    inherited_dir.mkdir(parents=True)

    original_personal = file_io.PERSONAL_DIR
    original_inherited = file_io.INHERITED_DIR

    file_io.PERSONAL_DIR = personal_dir
    file_io.INHERITED_DIR = inherited_dir

    yield personal_dir, inherited_dir

    file_io.PERSONAL_DIR = original_personal
    file_io.INHERITED_DIR = original_inherited


@pytest.fixture
def mock_personal_dir(tmp_path):
    """Setup mock personal directory only."""
    personal_dir = tmp_path / 'instincts' / 'personal'
    personal_dir.mkdir(parents=True)

    original_personal = file_io.PERSONAL_DIR
    original_inherited = file_io.INHERITED_DIR

    file_io.PERSONAL_DIR = personal_dir
    file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

    yield personal_dir

    file_io.PERSONAL_DIR = original_personal
    file_io.INHERITED_DIR = original_inherited


@pytest.mark.unit
class TestFileIOOperations:
    """Tests for file I/O operations."""

    def test_load_from_empty_directories(self, mock_directories):
        """Test loading from empty directories."""
        result = file_io.load_all_instincts()
        assert result == []

    @pytest.mark.parametrize("ext,file_id", [
        ('yaml', 'yaml-test'),
        ('yml', 'yml-test'),
        ('md', 'md-test'),
    ])
    def test_load_from_various_extensions(self, mock_personal_dir, ext, file_id):
        """Test loading from .yaml, .yml, and .md files."""
        content = f'''---
id: {file_id}
trigger: "test"
confidence: 0.8
---
Content'''
        (mock_personal_dir / f'test.{ext}').write_text(content)

        result = file_io.load_all_instincts()
        assert len(result) == 1
        assert result[0]['id'] == file_id

    def test_load_from_multiple_directories(self, mock_directories):
        """Test loading from both personal and inherited directories."""
        (mock_directories[0] / 'personal.yaml').write_text('---\nid: p\nconfidence: 0.8\n---\nP')
        (mock_directories[1] / 'inherited.yaml').write_text('---\nid: i\nconfidence: 0.7\n---\nI')

        result = file_io.load_all_instincts()
        assert len(result) == 2

        ids = [i['id'] for i in result]
        assert 'p' in ids
        assert 'i' in ids

        personal = next(i for i in result if i['id'] == 'p')
        inherited = next(i for i in result if i['id'] == 'i')
        assert personal['_source_type'] == 'personal'
        assert inherited['_source_type'] == 'inherited'

    def test_load_alphabetical_ordering(self, mock_personal_dir):
        """Test that files are loaded in alphabetical order."""
        for letter in ['c', 'a', 'b']:
            content = f'---\nid: {letter}\nconfidence: 0.5\n---\n{letter}'
            (mock_personal_dir / f'{letter}.yaml').write_text(content)

        result = file_io.load_all_instincts()
        assert len(result) == 3
        assert result[0]['id'] == 'a'
        assert result[1]['id'] == 'b'
        assert result[2]['id'] == 'c'

    def test_load_with_multiple_instincts_per_file(self, mock_personal_dir):
        """Test loading file with multiple instincts."""
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
        (mock_personal_dir / 'multi.yaml').write_text(content)

        result = file_io.load_all_instincts()
        assert len(result) == 2
        assert result[0]['id'] == 'first'
        assert result[1]['id'] == 'second'

    def test_source_metadata_added(self, mock_personal_dir):
        """Test that _source_file and _source_type metadata are added."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: test\nconfidence: 0.8\n---\nC')

        result = file_io.load_all_instincts()
        assert len(result) == 1
        assert '_source_file' in result[0]
        assert 'test.yaml' in result[0]['_source_file']
        assert result[0]['_source_type'] == 'personal'

    def test_load_with_corrupted_and_valid_files(self, mock_personal_dir):
        """Test that corrupted files don't crash, valid files still load."""
        (mock_personal_dir / 'valid.yaml').write_text('---\nid: valid\nconfidence: 0.8\n---\nV')
        (mock_personal_dir / 'corrupted.yaml').write_bytes(b'\x00\x01\x02\x03')

        result = file_io.load_all_instincts()
        assert len(result) >= 1
        assert any(i['id'] == 'valid' for i in result)

    def test_only_valid_extensions_loaded(self, mock_personal_dir):
        """Test that only .yaml, .yml, and .md files are loaded."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: yaml\nconfidence: 0.8\n---\nY')
        (mock_personal_dir / 'test.yml').write_text('---\nid: yml\nconfidence: 0.7\n---\nY')
        (mock_personal_dir / 'test.md').write_text('---\nid: md\nconfidence: 0.6\n---\nM')
        (mock_personal_dir / 'test.txt').write_text('---\nid: txt\nconfidence: 0.5\n---\nT')

        result = file_io.load_all_instincts()
        assert len(result) == 3
        ids = [i['id'] for i in result]
        assert 'yaml' in ids
        assert 'yml' in ids
        assert 'md' in ids
        assert 'txt' not in ids


@pytest.mark.unit
class TestFileIOPaths:
    """Tests for directory and file path constants."""

    def test_data_directories_exist(self):
        """Test that data directories are created."""
        assert file_io.DATA_DIR.exists()
        assert file_io.INSTINCTS_DIR.exists()
        assert file_io.PERSONAL_DIR.exists()
        assert file_io.INHERITED_DIR.exists()
        assert file_io.ARCHIVED_DIR.exists()

    def test_observation_file_path(self):
        """Test that observations file path is defined."""
        assert file_io.OBSERVATIONS_FILE.name == 'observations.jsonl'
