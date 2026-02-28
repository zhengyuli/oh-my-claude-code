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

    def test_import_with_min_confidence(self, temp_data_dir, temp_home):
        """Test import with minimum confidence filter."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        import_file = temp_data_dir / 'multi_confidence.yaml'
        import_content = '''---
id: minconf-high-confidence
trigger: "high"
confidence: 0.9
---
High confidence instinct.

---
id: minconf-low-confidence
trigger: "low"
confidence: 0.3
---
Low confidence instinct.
'''
        import_file.write_text(import_content)

        # Import with min confidence 0.5
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force', '--min-confidence', '0.5'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        # Only high confidence should be imported
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'status'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert 'minconf-high-confidence' in result.stdout
        assert 'minconf-low-confidence' not in result.stdout

    def test_export_by_domain(self, temp_data_dir, temp_home):
        """Test export filtered by domain."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        import_file = temp_data_dir / 'multi_domain.yaml'
        import_content = '''---
id: testing-instinct
trigger: "test"
confidence: 0.8
domain: testing
---
Testing instinct.

---
id: git-instinct
trigger: "git"
confidence: 0.7
domain: git
---
Git instinct.
'''
        import_file.write_text(import_content)

        subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        # Export only testing domain
        export_file = temp_data_dir / 'testing_only.yaml'
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'export',
             '--domain', 'testing', '--output', str(export_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        exported = export_file.read_text()
        assert 'testing-instinct' in exported
        assert 'git-instinct' not in exported

    def test_evolve_with_enough_instincts(self, temp_data_dir, temp_home):
        """Test evolve command with sufficient instincts."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        import_file = temp_data_dir / 'many.yaml'
        import_content = '''---
id: evolve-test-1
trigger: "when writing tests"
confidence: 0.85
domain: testing
---
Test instinct 1.

---
id: evolve-test-2
trigger: "when writing tests"
confidence: 0.80
domain: testing
---
Test instinct 2.

---
id: evolve-test-3
trigger: "when writing tests"
confidence: 0.75
domain: testing
---
Test instinct 3.

---
id: evolve-test-4
trigger: "when committing code"
confidence: 0.70
domain: git
---
Git instinct.
'''
        import_file.write_text(import_content)

        subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        # Evolve should work now
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'evolve'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        assert 'EVOLVE ANALYSIS' in result.stdout

    def test_duplicate_import_handling(self, temp_data_dir, temp_home):
        """Test that duplicate imports are handled correctly."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        import_file = temp_data_dir / 'dup.yaml'
        import_content = '''---
id: duplicate-test
trigger: "dup"
confidence: 0.7
---
Original.
'''
        import_file.write_text(import_content)

        # First import
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        # Second import with same ID but lower confidence
        import_content2 = '''---
id: duplicate-test
trigger: "dup"
confidence: 0.5
---
Lower confidence.
'''
        import_file.write_text(import_content2)

        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--force'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        # Should indicate skip or duplicate
        assert 'SKIP' in result.stdout or 'Nothing to import' in result.stdout or 'already exists' in result.stdout

    def test_import_dry_run(self, temp_data_dir, temp_home, sample_instinct_yaml):
        """Test import with --dry-run flag."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        import_file = temp_data_dir / 'import.yaml'
        import_file.write_text(sample_instinct_yaml)

        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py', 'import',
             str(import_file), '--dry-run'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        # Should show what would be imported
        assert 'DRY RUN' in result.stdout or 'dry' in result.stdout.lower()
