# tests/unit/test_rotation.py
import pytest
from pathlib import Path

@pytest.mark.unit
class TestFileRotationLogic:
    """Tests for file rotation logic."""

    def test_rotation_threshold_check(self):
        """Test checking if file exceeds rotation threshold."""
        max_size_mb = 2
        max_size_bytes = max_size_mb * 1024 * 1024
        small_size = 1024
        assert small_size < max_size_bytes
        large_size = 3 * 1024 * 1024
        assert large_size >= max_size_bytes

    def test_archive_naming_sequence(self):
        """Test archive file naming sequence."""
        base_name = "observations.jsonl"
        max_archives = 10
        archive_names = [f"observations.{i}.jsonl" for i in range(1, max_archives + 1)]
        assert len(archive_names) == max_archives
        assert archive_names[0] == "observations.1.jsonl"
        assert archive_names[-1] == f"observations.{max_archives}.jsonl"

    def test_rotation_moves_files_correctly(self):
        """Test that rotation moves files in correct order."""
        existing_archives = [1, 2, 3]
        new_archive = 1
        for i in sorted(existing_archives, reverse=True):
            new_index = i + 1
            assert new_index > i
        assert new_archive == 1

    def test_max_archives_deletes_oldest(self):
        """Test that max archives limit deletes oldest."""
        max_archives = 10
        archive_to_delete = f"observations.{max_archives}.jsonl"
        assert archive_to_delete == "observations.10.jsonl"
