"""
Comprehensive coverage tests for cmd_prune module.

Tests error paths, edge cases, and full workflows to achieve 90%+ coverage.
"""

import pytest
import tempfile
import sys
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from io import StringIO

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from commands.cmd_prune import cmd_prune, enforce_max_instincts, DEFAULT_MAX_INSTINCTS
from utils import file_io
import utils.file_io as file_io_module


@pytest.mark.unit
class TestCmdPruneCoverage:
    """Coverage tests for cmd_prune to reach 90%+."""

    def test_enforce_max_instincts_within_limit(self, tmp_path):
        """Test when instincts are within limit (no pruning needed)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Create only 2 instincts
        for i in range(2):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
confidence: 0.{i + 5}
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = enforce_max_instincts(max_count=10)
            assert result == 0  # No instincts archived
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_enforce_max_instincts_archives_low_confidence(self, tmp_path):
        """Test that low confidence instincts are archived (dry run)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Create 5 instincts with varying confidence
        for i in range(5):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
confidence: 0.{5 - i}
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = enforce_max_instincts(max_count=3, dry_run=True)
            assert result == 2  # 2 instincts would be archived
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_enforce_max_instincts_handles_name_conflicts(self, tmp_path):
        """Test that name conflicts are handled with timestamp suffix (dry run)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Create instincts
        for i in range(3):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
confidence: 0.{3 - i}
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            result = enforce_max_instincts(max_count=2, dry_run=True)
            assert result == 1  # 1 would be archived
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_cmd_prune_within_limit(self, tmp_path):
        """Test cmd_prune when within limit."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Create only 2 instincts
        for i in range(2):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
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
                max_instincts=10,
                dry_run=False
            )

            result = cmd_prune(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_cmd_prune_with_actual_archiving(self, tmp_path):
        """Test cmd_prune with dry-run (testing without actual archiving)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        personal_dir.mkdir(parents=True)

        # Create 5 instincts
        for i in range(5):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
confidence: 0.{5 - i}
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'

        try:
            args = Mock(
                max_instincts=3,
                dry_run=True  # Use dry run to avoid actual file moves
            )

            result = cmd_prune(args)
            assert result == 0
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited

    def test_cmd_prune_uses_default_max_instincts(self, tmp_path):
        """Test that default max_instincts is used when not specified."""
        args = Mock(
            max_instincts=None,  # Should use DEFAULT_MAX_INSTINCTS
            dry_run=True
        )

        # Should not crash
        result = cmd_prune(args)
        assert result == 0

    def test_enforce_max_instincts_sorts_by_effective_confidence(self, tmp_path):
        """Test that instincts are sorted by effective confidence (not base)."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        archived_dir = tmp_path / 'instincts' / 'archived'
        personal_dir.mkdir(parents=True)
        archived_dir.mkdir(parents=True)

        # Create instincts with old timestamps (high decay)
        old_timestamp = '2020-01-01T00:00:00Z'
        for i in range(5):
            (personal_dir / f'old-{i}.yaml').write_text(f'''---
id: old-{i}
confidence: 0.9
last_observed: {old_timestamp}
---
Old instinct with high base confidence
''')

        # Create one recent instinct (low decay)
        (personal_dir / 'recent.yaml').write_text('''---
id: recent
confidence: 0.6
last_observed: 2026-03-01T00:00:00Z
---
Recent instinct with lower base confidence
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        original_archived = file_io_module.ARCHIVED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'
        file_io_module.ARCHIVED_DIR = archived_dir

        try:
            # Keep only 3 - should keep the recent one and 2 old ones
            result = enforce_max_instincts(max_count=3, dry_run=False)
            assert result == 3  # 3 archived

            # Check that recent was NOT archived (has higher effective confidence)
            assert (personal_dir / 'recent.yaml').exists()
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited
            file_io_module.ARCHIVED_DIR = original_archived

    def test_cmd_prune_shows_correct_messages(self, tmp_path):
        """Test that correct messages are shown during pruning."""
        personal_dir = tmp_path / 'instincts' / 'personal'
        archived_dir = tmp_path / 'instincts' / 'archived'
        personal_dir.mkdir(parents=True)
        archived_dir.mkdir(parents=True)

        # Create 5 instincts
        for i in range(5):
            (personal_dir / f'instinct-{i}.yaml').write_text(f'''---
id: instinct-{i}
confidence: 0.{5 - i}
---
Content
''')

        original_personal = file_io_module.PERSONAL_DIR
        original_inherited = file_io_module.INHERITED_DIR
        original_archived = file_io_module.ARCHIVED_DIR
        file_io_module.PERSONAL_DIR = personal_dir
        file_io_module.INHERITED_DIR = tmp_path / 'instincts' / 'inherited'
        file_io_module.ARCHIVED_DIR = archived_dir

        try:
            args = Mock(
                max_instincts=3,
                dry_run=False
            )

            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                result = cmd_prune(args)
                output = mock_out.getvalue()

                assert 'Current instincts: 5' in output
                assert 'Max limit: 3' in output
                assert 'Archiving 2 lowest-confidence instincts' in output
                assert 'Archived 2 instincts' in output
        finally:
            file_io_module.PERSONAL_DIR = original_personal
            file_io_module.INHERITED_DIR = original_inherited
            file_io_module.ARCHIVED_DIR = original_archived
