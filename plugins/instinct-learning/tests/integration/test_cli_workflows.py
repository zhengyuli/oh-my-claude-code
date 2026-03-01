"""
Integration tests for complete CLI workflows.

This module tests end-to-end workflows including status, export, import,
and prune commands to achieve better coverage of command modules.
"""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils import file_io


@pytest.mark.integration
class TestCLIWorkflows:
    """Integration tests for CLI command workflows."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory for testing."""
        data_dir = tmp_path / 'instinct-data'
        personal_dir = data_dir / 'instincts' / 'personal'
        inherited_dir = data_dir / 'instincts' / 'inherited'
        archived_dir = data_dir / 'instincts' / 'archived'
        personal_dir.mkdir(parents=True)
        inherited_dir.mkdir(parents=True)
        archived_dir.mkdir(parents=True)

        # Create some test instincts
        instinct_content = '''---
id: test-instinct-1
trigger: "when running tests"
confidence: 0.85
domain: testing
---
# Test Instinct 1

## Action
Run all tests before committing.
'''
        (personal_dir / 'test-instinct-1.yaml').write_text(instinct_content)

        another_content = '''---
id: test-instinct-2
trigger: "when writing code"
confidence: 0.75
domain: workflow
---
# Test Instinct 2

## Action
Write tests first, then implementation.
'''
        (personal_dir / 'test-instinct-2.yaml').write_text(another_content)

        yield data_dir

        # Cleanup
        shutil.rmtree(data_dir, ignore_errors=True)

    def test_status_command_with_data_dir(self, temp_data_dir):
        """Test status command with custom data directory."""
        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'status'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert 'INSTINCT STATUS' in result.stdout
        assert 'test-instinct-1' in result.stdout or 'test-instinct-2' in result.stdout

    def test_export_command_to_file(self, temp_data_dir):
        """Test export command to a file."""
        cli_path = scripts_dir / 'instinct_cli.py'
        export_file = temp_data_dir / 'exported.md'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'export', '--output', str(export_file)],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert export_file.exists()
        content = export_file.read_text()
        assert 'test-instinct-1' in content or 'test-instinct-2' in content

    def test_export_command_with_domain_filter(self, temp_data_dir):
        """Test export command with domain filter."""
        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'export', '--domain', 'testing'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert 'test-instinct-1' in result.stdout  # Has domain: testing

    def test_export_command_with_min_confidence(self, temp_data_dir):
        """Test export command with minimum confidence filter."""
        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'export', '--min-confidence', '0.8'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        # Should only show test-instinct-1 (confidence 0.85)
        assert 'test-instinct-1' in result.stdout

    def test_export_import_workflow(self, temp_data_dir):
        """Test complete export then import workflow."""
        cli_path = scripts_dir / 'instinct_cli.py'
        export_file = temp_data_dir / 'exported.md'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        # Export
        export_result = subprocess.run(
            [sys.executable, str(cli_path), 'export', '--output', str(export_file)],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )
        assert export_result.returncode == 0

        # Import with dry-run
        import_result = subprocess.run(
            [sys.executable, str(cli_path), 'import', str(export_file), '--dry-run'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )
        assert import_result.returncode == 0
        assert 'DRY RUN' in import_result.stdout

    def test_prune_command_dry_run(self, temp_data_dir):
        """Test prune command with dry-run."""
        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'prune', '--max-instincts', '1', '--dry-run'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert 'DRY RUN' in result.stdout or 'would archive' in result.stdout.lower()

    def test_decay_command(self, temp_data_dir):
        """Test decay command."""
        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'decay'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert 'CONFIDENCE DECAY ANALYSIS' in result.stdout

    def test_status_with_no_instincts(self, tmp_path):
        """Test status command when no instincts exist."""
        empty_dir = tmp_path / 'empty-instincts'
        personal_dir = empty_dir / 'instincts' / 'personal'
        inherited_dir = empty_dir / 'instincts' / 'inherited'
        personal_dir.mkdir(parents=True)
        inherited_dir.mkdir(parents=True)

        cli_path = scripts_dir / 'instinct_cli.py'
        env = {'INSTINCT_LEARNING_DATA_DIR': str(empty_dir)}

        result = subprocess.run(
            [sys.executable, str(cli_path), 'status'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, **env}
        )

        assert result.returncode == 0
        assert 'No instincts found' in result.stdout


@pytest.mark.integration
class TestCommandModuleImports:
    """Direct imports and testing of command modules."""

    def test_status_command_module(self):
        """Test cmd_status module directly."""
        from argparse import Namespace
        from commands.cmd_status import cmd_status

        # Create a mock args object
        args = Namespace()

        # Should not crash
        result = cmd_status(args)
        assert result == 0

    def test_export_command_module(self):
        """Test cmd_export module directly."""
        from argparse import Namespace
        from commands.cmd_export import cmd_export
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            export_file = f.name

        try:
            args = Namespace(output=export_file, domain=None, min_confidence=None)

            result = cmd_export(args)
            # Result depends on whether there are instincts to export
            assert isinstance(result, int)
        finally:
            Path(export_file).unlink(missing_ok=True)

    def test_import_command_module_with_file(self, tmp_path):
        """Test cmd_import module with a file."""
        from argparse import Namespace
        from commands.cmd_import import cmd_import

        # Create a test import file
        import_file = tmp_path / 'import.md'
        import_content = '''---
id: imported-instinct
trigger: "test import"
confidence: 0.7
domain: testing
---
Imported content
'''
        import_file.write_text(import_content)

        args = Namespace(
            source=str(import_file),
            dry_run=True,
            force=True,
            min_confidence=0.0
        )

        result = cmd_import(args)
        assert result == 0

    def test_prune_command_module(self):
        """Test cmd_prune module directly."""
        from argparse import Namespace
        from commands.cmd_prune import cmd_prune

        args = Namespace(max_instincts=100, dry_run=True)

        result = cmd_prune(args)
        assert result == 0

    def test_decay_command_module(self):
        """Test cmd_decay module directly."""
        from argparse import Namespace
        from commands.cmd_decay import cmd_decay

        args = Namespace(decay_rate=None)

        result = cmd_decay(args)
        assert result == 0

    def test_cli_parser_module(self):
        """Test cli_parser module."""
        from cli_parser import parse_args, create_parser

        # Test parsing status command
        args = parse_args(['status'])
        assert args.command == 'status'

        # Test parsing export command
        args = parse_args(['export', '--output', 'test.md'])
        assert args.command == 'export'
        assert args.output == 'test.md'

        # Test parsing import command
        args = parse_args(['import', 'test.md', '--dry-run'])
        assert args.command == 'import'
        assert args.dry_run is True

        # Test parser creation
        parser = create_parser()
        assert parser is not None
