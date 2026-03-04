"""
Comprehensive coverage tests for cmd_export, cmd_decay, and cmd_status modules.

Tests error paths, edge cases, and filtering scenarios to achieve 90%+ coverage.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO
import os

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from commands.cmd_export import cmd_export
from commands.cmd_decay import cmd_decay
from commands.cmd_status import cmd_status
from utils import file_io
import utils.file_io as file_io_module


@pytest.mark.unit
class TestCmdExportCoverage:
    """Coverage tests for cmd_export to reach 90%+."""

    def test_export_with_no_instincts(self, tmp_path):
        """Test export when there are no instincts."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                output=None,  # Print to stdout
                domain=None,
                min_confidence=None
            )

            result = cmd_export(args)
            assert result == 1  # No instincts to export
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_export_with_domain_filter_no_matches(self, tmp_path):
        """Test export with domain filter that matches nothing."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
domain: testing
confidence: 0.8
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                output=None,
                domain='workflow',  # No instincts with this domain
                min_confidence=None
            )

            result = cmd_export(args)
            assert result == 1  # No instincts match
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_export_with_min_confidence_no_matches(self, tmp_path):
        """Test export with min_confidence that matches nothing."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
domain: testing
confidence: 0.7
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                output=None,
                domain=None,
                min_confidence=0.9  # No instincts this high
            )

            result = cmd_export(args)
            assert result == 1  # No instincts match
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_export_to_stdout(self, tmp_path):
        """Test export to stdout (no output file)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
domain: testing
confidence: 0.8
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                output=None,
                domain=None,
                min_confidence=None
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_export(args)
                output = mock_out.getvalue()

                assert result == 0
                assert 'test-instinct' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_export_with_source_repo_field(self, tmp_path):
        """Test export with source_repo field included."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
domain: testing
confidence: 0.8
source_repo: https://github.com/example/repo
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                output=None,
                domain=None,
                min_confidence=None
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_export(args)
                output = mock_out.getvalue()

                assert result == 0
                assert 'source_repo' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited


@pytest.mark.unit
class TestCmdDecayCoverage:
    """Coverage tests for cmd_decay to reach 90%+."""

    def test_decay_with_no_instincts(self, tmp_path):
        """Test decay command when there are no instincts."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(decay_rate=None)

            result = cmd_decay(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_decay_with_custom_rate(self, tmp_path):
        """Test decay with custom decay rate."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
confidence: 0.8
last_observed: 2026-02-01T00:00:00Z
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(decay_rate=0.1)  # 10% weekly decay

            result = cmd_decay(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_decay_shows_no_decay_for_recent(self, tmp_path):
        """Test that recent instincts show no decay."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
confidence: 0.8
last_observed: 2026-03-01T00:00:00Z
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(decay_rate=None)

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_decay(args)
                output = mock_out.getvalue()

                assert result == 0
                assert 'no decay' in output.lower()
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited


@pytest.mark.unit
class TestCmdStatusCoverage:
    """Coverage tests for cmd_status to reach 90%+."""

    def test_status_with_no_instincts(self, tmp_path):
        """Test status when there are no instincts."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                domain=None,
                min_confidence=None
            )

            result = cmd_status(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_status_shows_domain_grouping(self, tmp_path):
        """Test that instincts are grouped by domain."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test1.yaml').write_text('''---
id: test-1
domain: testing
confidence: 0.8
---
Content
''')

        (personal_dir / 'test2.yaml').write_text('''---
id: test-2
domain: workflow
confidence: 0.7
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                domain=None,
                min_confidence=None
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_status(args)
                output = mock_out.getvalue()

                assert result == 0
                assert 'TESTING' in output
                assert 'WORKFLOW' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_status_shows_confidence_bar(self, tmp_path):
        """Test that confidence bar is displayed correctly."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: test-instinct
domain: testing
confidence: 0.85
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                domain=None,
                min_confidence=None
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_status(args)
                output = mock_out.getvalue()

                assert result == 0
                # 85% confidence should show 8 blocks (█████████)
                assert '█' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_status_shows_personal_vs_inherited_counts(self, tmp_path):
        """Test that personal and inherited counts are shown separately."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        inherited_dir = tmp_path / 'instincts' / 'inherited'
        personal_dir.mkdir(parents=True)
        inherited_dir.mkdir(parents=True)

        (personal_dir / 'test.yaml').write_text('''---
id: personal-instinct
confidence: 0.8
---
Content
''')

        (inherited_dir / 'test.yaml').write_text('''---
id: inherited-instinct
confidence: 0.7
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = inherited_dir

        try:
            args = Mock(
                domain=None,
                min_confidence=None
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_status(args)
                output = mock_out.getvalue()

                assert result == 0
                assert 'Personal:  1' in output
                assert 'Inherited: 1' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited
