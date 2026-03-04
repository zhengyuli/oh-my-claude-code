"""
Coverage tests for cmd_export, cmd_import, cmd_decay, and cmd_status modules.

Optimized version with parametrize and fixtures to reduce code duplication.
"""

import pytest
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from commands.cmd_export import cmd_export
from commands.cmd_import import cmd_import
from commands.cmd_decay import cmd_decay
from commands.cmd_status import cmd_status
import utils.file_io as file_io_module


@pytest.fixture
def mock_directories(tmp_path):
    """Setup and return mock directories, auto cleanup."""
    personal_dir = tmp_path / 'instincts' / 'personal'
    inherited_dir = tmp_path / 'instincts' / 'inherited'
    personal_dir.mkdir(parents=True)
    inherited_dir.mkdir(parents=True)

    original_personal = file_io_module.PERSONAL_DIR
    original_inherited = file_io_module.INHERITED_DIR

    file_io_module.PERSONAL_DIR = personal_dir
    file_io_module.INHERITED_DIR = inherited_dir

    yield personal_dir, inherited_dir

    file_io_module.PERSONAL_DIR = original_personal
    file_io_module.INHERITED_DIR = original_inherited


@pytest.fixture
def mock_personal_dir(tmp_path):
    """Setup mock personal directory only."""
    personal_dir = tmp_path / 'instincts' / 'personal'
    personal_dir.mkdir(parents=True)

    original_personal = file_io_module.PERSONAL_DIR
    original_inherited = file_io_module.INHERITED_DIR

    file_io_module.PERSONAL_DIR = personal_dir
    file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

    yield personal_dir

    file_io_module.PERSONAL_DIR = original_personal
    file_io_module.INHERITED_DIR = original_inherited


@pytest.mark.unit
class TestCmdExportCoverage:
    """Coverage tests for cmd_export."""

    def test_export_with_no_instincts(self, mock_personal_dir):
        """Test export when there are no instincts."""
        args = Mock(output=None, domain=None, min_confidence=None)
        result = cmd_export(args)
        assert result == 1

    @pytest.mark.parametrize("filter_type,filter_value,setup_content", [
        ('domain', 'workflow', 'domain: testing\nconfidence: 0.8\n'),
        ('min_confidence', 0.9, 'domain: testing\nconfidence: 0.7\n'),
    ])
    def test_export_with_no_matches(self, mock_personal_dir, filter_type, filter_value, setup_content):
        """Test export with filter that matches nothing."""
        (mock_personal_dir / 'test.yaml').write_text(f'---\nid: test\n{setup_content}---\nContent')

        if filter_type == 'domain':
            args = Mock(output=None, domain=filter_value, min_confidence=None)
        else:
            args = Mock(output=None, domain=None, min_confidence=filter_value)

        result = cmd_export(args)
        assert result == 1

    def test_export_to_stdout(self, mock_personal_dir):
        """Test export to stdout."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: test-instinct\ndomain: testing\nconfidence: 0.8\n---\nContent')

        args = Mock(output=None, domain=None, min_confidence=None)

        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            result = cmd_export(args)
            output = mock_out.getvalue()
            assert result == 0
            assert 'test-instinct' in output


@pytest.mark.unit
class TestCmdImportCoverage:
    """Coverage tests for cmd_import."""

    def test_import_from_nonexistent_file(self, tmp_path):
        """Test importing from a file that doesn't exist."""
        args = Mock(source=str(tmp_path / 'does-not-exist.md'), dry_run=False, force=True, min_confidence=0.0)
        result = cmd_import(args)
        assert result == 1

    def test_import_from_file_with_no_valid_instincts(self, tmp_path):
        """Test importing from a file with no valid instincts."""
        import_file = tmp_path / 'invalid.md'
        import_file.write_text('No frontmatter here\nJust plain text')

        args = Mock(source=str(import_file), dry_run=False, force=True, min_confidence=0.0)
        result = cmd_import(args)
        assert result == 1

    def test_import_with_min_confidence_filter(self, tmp_path):
        """Test import with min_confidence filtering out all instincts."""
        import_file = tmp_path / 'low-conf.md'
        import_file.write_text('---\nid: low-conf\ntrigger: "test"\nconfidence: 0.1\n---\nContent')

        args = Mock(source=str(import_file), dry_run=True, force=True, min_confidence=0.5)
        result = cmd_import(args)
        assert result == 0

    @pytest.mark.parametrize("conf_diff,should_update", [
        (0.1, False),  # Lower confidence, skip
        (0.2, True),   # Higher confidence, update
    ])
    def test_import_duplicate_handling(self, mock_directories, conf_diff, should_update):
        """Test import duplicate handling based on confidence."""
        import_file = mock_directories[1].parent / f'{"update" if should_update else "skip"}.md'
        existing_conf = 0.8 if should_update else 0.7
        new_conf = existing_conf + (0.1 if should_update else -0.1)

        import_file.write_text(f'---\nid: existing\ntrigger: "test"\nconfidence: {new_conf}\n---\nNew content')
        (mock_directories[0] / 'existing.yaml').write_text(f'---\nid: existing\ntrigger: "test"\nconfidence: {existing_conf}\n---\nOld content')

        args = Mock(source=str(import_file), dry_run=True, force=True, min_confidence=0.0)
        result = cmd_import(args)
        assert result == 0

    def test_import_with_confirmation(self, mock_directories):
        """Test import confirmation flow (accept)."""
        import_file = mock_directories[1].parent / 'new.md'
        import_file.write_text('---\nid: new\ntrigger: "test"\nconfidence: 0.8\n---\nContent')

        args = Mock(source=str(import_file), dry_run=False, force=False, min_confidence=0.0)

        with patch('builtins.input', return_value='y'):
            result = cmd_import(args)
            assert result == 0

    @patch('urllib.request.urlopen')
    def test_import_from_url(self, mock_urlopen, mock_directories):
        """Test successful import from URL."""
        mock_response = Mock()
        mock_response.read.return_value = b'---\nid: url-instinct\ntrigger: "test"\nconfidence: 0.8\n---\nContent'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        args = Mock(source='https://example.com/instincts.md', dry_run=True, force=True, min_confidence=0.0)
        result = cmd_import(args)
        assert result == 0

    @patch('urllib.request.urlopen')
    def test_import_from_url_error(self, mock_urlopen):
        """Test import from URL with error."""
        mock_urlopen.side_effect = urllib.error.URLError('Network error')
        args = Mock(source='https://example.com/instincts.md', dry_run=False, force=True, min_confidence=0.0)
        result = cmd_import(args)
        assert result == 1


@pytest.mark.unit
class TestCmdDecayCoverage:
    """Coverage tests for cmd_decay."""

    def test_decay_with_no_instincts(self, mock_personal_dir):
        """Test decay command when there are no instincts."""
        args = Mock(decay_rate=None)
        result = cmd_decay(args)
        assert result == 0

    def test_decay_with_custom_rate(self, mock_personal_dir):
        """Test decay with custom decay rate."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: test\nconfidence: 0.8\nlast_observed: 2026-02-01T00:00:00Z\n---\nContent')

        args = Mock(decay_rate=0.1)
        result = cmd_decay(args)
        assert result == 0

    def test_decay_shows_no_decay_for_recent(self, mock_personal_dir):
        """Test that recent instincts show no decay."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: test\nconfidence: 0.8\nlast_observed: 2026-03-01T00:00:00Z\n---\nContent')

        args = Mock(decay_rate=None)

        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            result = cmd_decay(args)
            output = mock_out.getvalue()
            assert result == 0
            assert 'no decay' in output.lower()


@pytest.mark.unit
class TestCmdStatusCoverage:
    """Coverage tests for cmd_status."""

    def test_status_with_no_instincts(self, mock_personal_dir):
        """Test status when there are no instincts."""
        args = Mock(domain=None, min_confidence=None)
        result = cmd_status(args)
        assert result == 0

    def test_status_shows_domain_grouping(self, mock_personal_dir):
        """Test that instincts are grouped by domain."""
        (mock_personal_dir / 'test1.yaml').write_text('---\nid: test-1\ndomain: testing\nconfidence: 0.8\n---\nContent')
        (mock_personal_dir / 'test2.yaml').write_text('---\nid: test-2\ndomain: workflow\nconfidence: 0.7\n---\nContent')

        args = Mock(domain=None, min_confidence=None)

        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            result = cmd_status(args)
            output = mock_out.getvalue()
            assert result == 0
            assert 'TESTING' in output
            assert 'WORKFLOW' in output

    def test_status_shows_confidence_bar(self, mock_personal_dir):
        """Test that confidence bar is displayed correctly."""
        (mock_personal_dir / 'test.yaml').write_text('---\nid: test\ndomain: testing\nconfidence: 0.85\n---\nContent')

        args = Mock(domain=None, min_confidence=None)

        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            result = cmd_status(args)
            output = mock_out.getvalue()
            assert result == 0
            assert '█' in output

    def test_status_shows_personal_vs_inherited_counts(self, mock_directories):
        """Test that personal and inherited counts are shown separately."""
        (mock_directories[0] / 'test.yaml').write_text('---\nid: personal\nconfidence: 0.8\n---\nContent')
        (mock_directories[1] / 'test.yaml').write_text('---\nid: inherited\nconfidence: 0.7\n---\nContent')

        args = Mock(domain=None, min_confidence=None)

        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            result = cmd_status(args)
            output = mock_out.getvalue()
            assert result == 0
            assert 'Personal:  1' in output
            assert 'Inherited: 1' in output
