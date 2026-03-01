"""
Tests for the main instinct_cli.py entry point.

Covers the main() function and command routing.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))


@pytest.mark.unit
class TestInstinctCliMain:
    """Tests for instinct_cli.py main entry point."""

    def test_main_help_command(self):
        """Test main with no command shows help."""
        with patch('sys.argv', ['instinct_cli.py']):
            from instinct_cli import main

            result = main()
            assert result == 1  # Help returns 1

    def test_main_status_command(self):
        """Test main routes to status command."""
        with patch('sys.argv', ['instinct_cli.py', 'status']):
            from instinct_cli import main

            result = main()
            assert result == 0  # Success

    def test_main_export_command(self):
        """Test main routes to export command."""
        with patch('sys.argv', ['instinct_cli.py', 'export']):
            from instinct_cli import main

            result = main()
            assert result in [0, 1]  # Either success or no instincts

    def test_main_import_command_with_file(self, tmp_path):
        """Test main routes to import command."""
        import_file = tmp_path / 'test.md'
        import_file.write_text('''---
id: test
trigger: "test"
confidence: 0.8
---
Content
''')

        with patch('sys.argv', ['instinct_cli.py', 'import', str(import_file), '--dry-run']):
            from instinct_cli import main

            result = main()
            assert result == 0  # Success (dry run)

    def test_main_prune_command(self):
        """Test main routes to prune command."""
        with patch('sys.argv', ['instinct_cli.py', 'prune', '--dry-run']):
            from instinct_cli import main

            result = main()
            assert result == 0  # Success

    def test_main_decay_command(self):
        """Test main routes to decay command."""
        with patch('sys.argv', ['instinct_cli.py', 'decay']):
            from instinct_cli import main

            result = main()
            assert result == 0  # Success

    def test_main_invalid_command(self):
        """Test main with invalid command shows help."""
        with patch('sys.argv', ['instinct_cli.py', 'invalid']):
            from instinct_cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Help exits with code 2
            assert exc_info.value.code == 2
