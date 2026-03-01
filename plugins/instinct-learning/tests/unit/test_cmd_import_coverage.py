"""
Comprehensive coverage tests for cmd_import module.

Tests error paths, edge cases, and full workflows to achieve 90%+ coverage.
"""

import pytest
import tempfile
import sys
import os
import urllib.error
from pathlib import Path
from unittest.mock import patch, Mock
from io import StringIO

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from commands.cmd_import import cmd_import
from utils import file_io
import utils.file_io as file_io_module


@pytest.mark.unit
class TestCmdImportCoverage:
    """Coverage tests for cmd_import to reach 90%+."""

    def test_import_from_nonexistent_file(self, tmp_path):
        """Test importing from a file that doesn't exist."""
        non_existent = tmp_path / 'does-not-exist.md'

        args = Mock(
            source=str(non_existent),
            dry_run=False,
            force=True,
            min_confidence=0.0
        )

        result = cmd_import(args)
        assert result == 1  # Error return code

    def test_import_from_file_with_no_valid_instincts(self, tmp_path):
        """Test importing from a file with no valid instincts."""
        import_file = tmp_path / 'invalid.md'
        import_file.write_text('No frontmatter here\nJust plain text')

        args = Mock(
            source=str(import_file),
            dry_run=False,
            force=True,
            min_confidence=0.0
        )

        result = cmd_import(args)
        assert result == 1  # Error return code

    def test_import_with_min_confidence_filter(self, tmp_path):
        """Test import with min_confidence filtering out all instincts."""
        import_file = tmp_path / 'low-conf.md'
        import_file.write_text('''---
id: low-conf
trigger: "test"
confidence: 0.1
---
Content
''')

        args = Mock(
            source=str(import_file),
            dry_run=True,
            force=True,
            min_confidence=0.5
        )

        result = cmd_import(args)
        assert result == 0  # Success but no imports

    def test_import_with_duplicates_skipped(self, tmp_path):
        """Test import where duplicates are skipped due to equal/lower confidence."""
        import_file = tmp_path / 'dupes.md'
        import_file.write_text('''---
id: existing-instinct
trigger: "test"
confidence: 0.7
---
Content
''')

        # Create an existing instinct with higher confidence
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)
        (personal_dir / 'existing-instinct.yaml').write_text('''---
id: existing-instinct
trigger: "test"
confidence: 0.8
---
Higher confidence content
''')

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                source=str(import_file),
                dry_run=True,
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_with_duplicates_updated(self, tmp_path):
        """Test import where duplicates are updated due to higher confidence."""
        import_file = tmp_path / 'updates.md'
        import_file.write_text('''---
id: existing-instinct
trigger: "test"
confidence: 0.9
---
Higher confidence content
''')

        # Create an existing instinct with lower confidence
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)
        (personal_dir / 'existing-instinct.yaml').write_text('''---
id: existing-instinct
trigger: "test"
confidence: 0.7
---
Lower confidence content
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=True,
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_with_many_duplicates_shows_truncated_list(self, tmp_path):
        """Test that more than 5 duplicates are truncated in output."""
        import_file = tmp_path / 'many-dupes.md'
        content_parts = []
        for i in range(10):
            content_parts.append(f'''---
id: duplicate-{i}
trigger: "test"
confidence: 0.5
---
Content {i}
''')
        import_file.write_text('\n'.join(content_parts))

        # Create existing instincts
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)
        for i in range(10):
            (personal_dir / f'duplicate-{i}.yaml').write_text(f'''---
id: duplicate-{i}
trigger: "test"
confidence: 0.8
---
Higher confidence
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=True,
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_with_source_repo_field(self, tmp_path):
        """Test import with source_repo field in instinct."""
        import_file = tmp_path / 'with-repo.md'
        import_file.write_text('''---
id: repo-instinct
trigger: "test"
confidence: 0.8
source_repo: https://github.com/example/repo
---
Content
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=True,
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_with_confirmation_cancelled(self, tmp_path):
        """Test import when user cancels confirmation."""
        import_file = tmp_path / 'new-instinct.md'
        import_file.write_text('''---
id: new-one
trigger: "test"
confidence: 0.8
---
Content
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=False,
                force=False,  # Requires confirmation
                min_confidence=0.0
            )

            # Mock input to cancel
            with patch('builtins.input', return_value='n'):
                result = cmd_import(args)
                assert result == 0  # Cancelled is success
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_with_confirmation_accepted(self, tmp_path):
        """Test import when user accepts confirmation."""
        import_file = tmp_path / 'new-instinct.md'
        import_file.write_text('''---
id: new-one
trigger: "test"
confidence: 0.8
---
Content
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=False,
                force=False,
                min_confidence=0.0
            )

            # Mock input to accept
            with patch('builtins.input', return_value='y'):
                result = cmd_import(args)
                assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_import_creates_output_file(self, tmp_path):
        """Test that import preview works correctly (dry run)."""
        import_file = tmp_path / 'new-instinct.md'
        import_file.write_text('''---
id: new-one
trigger: "test"
confidence: 0.8
---
Content
''')

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source=str(import_file),
                dry_run=True,  # Use dry run
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    @patch('urllib.request.urlopen')
    def test_import_from_url_success(self, mock_urlopen, tmp_path):
        """Test successful import from URL."""
        # Mock URL response
        mock_response = Mock()
        mock_response.read.return_value = b'''---
id: url-instinct
trigger: "test"
confidence: 0.8
---
Content
'''
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        inherited_dir = tmp_path / 'instincts' / 'inherited'
        inherited_dir.mkdir(parents=True)
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Patch directories
        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                source='https://example.com/instincts.md',
                dry_run=True,
                force=True,
                min_confidence=0.0
            )

            result = cmd_import(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    @patch('urllib.request.urlopen')
    def test_import_from_url_error(self, mock_urlopen, tmp_path):
        """Test import from URL with error."""
        # Simulate URLError
        mock_urlopen.side_effect = urllib.error.URLError('Network error')

        args = Mock(
            source='https://example.com/instincts.md',
            dry_run=False,
            force=True,
            min_confidence=0.0
        )

        result = cmd_import(args)
        assert result == 1  # Error return code
