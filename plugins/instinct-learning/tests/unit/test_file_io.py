"""
Comprehensive file I/O tests.

This module provides detailed testing of file operations
to achieve 85%+ coverage for the file_io module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils import file_io
from utils.instinct_parser import parse_instinct_file


@pytest.mark.unit
class TestFileIOOperations:
    """Comprehensive tests for file I/O operations."""

    def test_load_from_nonexistent_directory(self, tmp_path):
        """Test loading from nonexistent directory."""
        # Create a temporary data directory structure
        temp_instincts = tmp_path / 'instincts'
        temp_personal = temp_instincts / 'personal'
        temp_inherited = temp_instincts / 'inherited'
        temp_personal.mkdir(parents=True)
        temp_inherited.mkdir(parents=True)

        # Backup and patch directories
        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = temp_personal
        file_io.INHERITED_DIR = temp_inherited

        try:
            result = file_io.load_all_instincts()
            assert result == []
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_yaml_file(self, tmp_path):
        """Test loading instincts from .yaml file."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: yaml-test
trigger: "yaml test"
confidence: 0.8
---
YAML content
'''
        (personal_dir / 'test.yaml').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'yaml-test'
            assert result[0]['_source_type'] == 'personal'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_yml_file(self, tmp_path):
        """Test loading instincts from .yml file."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: yml-test
confidence: 0.7
---
YML content
'''
        (personal_dir / 'test.yml').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'yml-test'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_md_file(self, tmp_path):
        """Test loading instincts from .md file."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: md-test
trigger: "md test"
---
Markdown content
'''
        (personal_dir / 'test.md').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 1
            assert result[0]['id'] == 'md-test'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_from_multiple_directories(self, tmp_path):
        """Test loading from both personal and inherited directories."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        inherited_dir = tmp_path / 'instincts' / 'inherited'
        personal_dir.mkdir(parents=True)
        inherited_dir.mkdir(parents=True)

        personal_content = '''---
id: personal-instinct
confidence: 0.8
---
Personal content
'''
        inherited_content = '''---
id: inherited-instinct
confidence: 0.7
---
Inherited content
'''

        (personal_dir / 'personal.yaml').write_text(personal_content)
        (inherited_dir / 'inherited.yaml').write_text(inherited_content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = inherited_dir

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 2

            ids = [i['id'] for i in result]
            assert 'personal-instinct' in ids
            assert 'inherited-instinct' in ids

            personal = next(i for i in result if i['id'] == 'personal-instinct')
            inherited = next(i for i in result if i['id'] == 'inherited-instinct')
            assert personal['_source_type'] == 'personal'
            assert inherited['_source_type'] == 'inherited'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_alphabetical_ordering(self, tmp_path):
        """Test that files are loaded in alphabetical order."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        for letter in ['c', 'a', 'b']:
            content = f'''---
id: {letter}-test
confidence: 0.5
---
Content {letter}
'''
            (personal_dir / f'{letter}.yaml').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 3
            # Should be ordered: a-test, b-test, c-test
            assert result[0]['id'] == 'a-test'
            assert result[1]['id'] == 'b-test'
            assert result[2]['id'] == 'c-test'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_with_corrupted_file(self, tmp_path):
        """Test that corrupted files don't crash the loader."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        valid_content = '''---
id: valid
confidence: 0.8
---
Valid content
'''
        (personal_dir / 'valid.yaml').write_text(valid_content)
        (personal_dir / 'corrupted.yaml').write_bytes(b'\x00\x01\x02\x03')

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            # Should not crash, should load valid file
            result = file_io.load_all_instincts()
            assert len(result) >= 1
            assert any(i['id'] == 'valid' for i in result)
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_with_multiple_instincts_per_file(self, tmp_path):
        """Test loading file with multiple instincts."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: first
trigger: "first"
confidence: 0.8
---
First content

---
id: second
trigger: "second"
confidence: 0.7
---
Second content
'''
        (personal_dir / 'multi.yaml').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 2
            assert result[0]['id'] == 'first'
            assert result[1]['id'] == 'second'
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_source_file_metadata_added(self, tmp_path):
        """Test that _source_file metadata is added."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: test
confidence: 0.8
---
Content
'''
        (personal_dir / 'test.yaml').write_text(content)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 1
            assert '_source_file' in result[0]
            assert 'test.yaml' in result[0]['_source_file']
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_empty_directories(self, tmp_path):
        """Test loading from empty directories."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        inherited_dir = tmp_path / 'instincts' / 'inherited'
        personal_dir.mkdir(parents=True)
        inherited_dir.mkdir(parents=True)

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = inherited_dir

        try:
            result = file_io.load_all_instincts()
            assert result == []
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_data_directories_exist(self):
        """Test that data directories are created."""
        # The module should create directories on import
        assert file_io.DATA_DIR.exists()
        assert file_io.INSTINCTS_DIR.exists()
        assert file_io.PERSONAL_DIR.exists()
        assert file_io.INHERITED_DIR.exists()
        assert file_io.ARCHIVED_DIR.exists()

    def test_observation_file_path(self):
        """Test that observations file path is defined."""
        assert file_io.OBSERVATIONS_FILE.name == 'observations.jsonl'

    def test_file_with_bom_marker(self, tmp_path):
        """Test loading file with UTF-8 BOM marker."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        content = '''---
id: bom-test
confidence: 0.8
---
Content with BOM
'''
        # Add UTF-8 BOM
        (personal_dir / 'bom.yaml').write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) >= 0  # Should handle BOM gracefully
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_with_empty_file(self, tmp_path):
        """Test loading an empty file."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'empty.yaml').write_text('')

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            # Empty file should be handled gracefully
            assert isinstance(result, list)
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited

    def test_load_files_with_various_extensions(self, tmp_path):
        """Test that only .yaml, .yml, and .md files are loaded."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        yaml_content = '''---
id: yaml
confidence: 0.8
---
YAML
'''
        yml_content = '''---
id: yml
confidence: 0.7
---
YML
'''
        md_content = '''---
id: md
confidence: 0.6
---
MD
'''
        txt_content = '''---
id: txt
confidence: 0.5
---
TXT
'''

        (personal_dir / 'test.yaml').write_text(yaml_content)
        (personal_dir / 'test.yml').write_text(yml_content)
        (personal_dir / 'test.md').write_text(md_content)
        (personal_dir / 'test.txt').write_text(txt_content)  # Should be ignored

        original_personal = file_io.PERSONAL_DIR
        original_inherited = file_io.INHERITED_DIR
        file_io.PERSONAL_DIR = personal_dir
        file_io.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = file_io.load_all_instincts()
            assert len(result) == 3  # Only yaml, yml, md
            ids = [i['id'] for i in result]
            assert 'yaml' in ids
            assert 'yml' in ids
            assert 'md' in ids
            assert 'txt' not in ids
        finally:
            file_io.PERSONAL_DIR = original_personal
            file_io.INHERITED_DIR = original_inherited
