"""Integration tests for CLI commands.

Tests complete CLI workflows using subprocess to ensure commands
work as expected in real execution contexts.
"""

import os
import pytest
import subprocess
import sys
from pathlib import Path


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_status_with_no_instincts(self, temp_data_dir, temp_home, monkeypatch):
        """Test status command when no instincts exist."""
        # The temp_home fixture already set the environment via monkeypatch
        # We need to capture that for subprocess
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'status'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert 'No instincts found' in result.stdout or 'INSTINCT STATUS' in result.stdout

    def test_import_and_status_workflow(self, temp_data_dir, temp_home, sample_instinct_yaml):
        """Test importing an instinct and checking status."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        # Create import file
        import_file = temp_data_dir / 'import.yaml'
        import_file.write_text(sample_instinct_yaml)

        # Import
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert 'Import complete' in result.stdout or 'imported' in result.stdout.lower()

        # Check status
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'status'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert 'test-instinct' in result.stdout

    def test_export_after_import(self, temp_data_dir, temp_home, sample_instinct_yaml):
        """Test exporting after importing."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        # Import first
        import_file = temp_data_dir / 'import.yaml'
        import_file.write_text(sample_instinct_yaml)
        subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        # Export
        export_file = temp_data_dir / 'export.yaml'
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'export',
             '--output', str(export_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert export_file.exists()
        content = export_file.read_text()
        assert 'test-instinct' in content

    def test_evolve_with_insufficient_instincts(self, temp_data_dir, temp_home):
        """Test evolve command with insufficient instincts."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'evolve'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert 'at least 3' in result.stdout.lower() or 'need' in result.stdout.lower()

    def test_decay_command_output(self, temp_data_dir, temp_home, sample_instinct_yaml):
        """Test decay command shows output."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        # Import an instinct first
        import_file = temp_data_dir / 'import.yaml'
        import_file.write_text(sample_instinct_yaml)
        subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        # Run decay
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'decay'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert 'CONFIDENCE DECAY' in result.stdout or 'test-instinct' in result.stdout
