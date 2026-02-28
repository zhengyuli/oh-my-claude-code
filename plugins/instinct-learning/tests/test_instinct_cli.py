#!/usr/bin/env python3
"""
Unit tests for instinct_cli.py

Run with: python3 tests/test_instinct_cli.py
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from instinct_cli import (
    parse_instinct_file,
    load_all_instincts,
)


class TestParseInstinctFile(unittest.TestCase):
    """Tests for parse_instinct_file function."""

    def test_parse_single_instinct(self):
        """Test parsing a single instinct with all fields."""
        content = '''---
id: test-instinct
trigger: "when testing code"
confidence: 0.85
domain: testing
source: session-observation
---
# Test Instinct

## Action
Run tests before committing.

## Evidence
- Observed 5 times in session abc123
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'test-instinct')
        self.assertEqual(result[0]['trigger'], 'when testing code')
        self.assertEqual(result[0]['confidence'], 0.85)
        self.assertEqual(result[0]['domain'], 'testing')
        self.assertIn('Test Instinct', result[0]['content'])
        self.assertIn('Run tests before committing', result[0]['content'])

    def test_parse_multiple_instincts(self):
        """Test parsing multiple instincts in one file."""
        content = '''---
id: first-instinct
trigger: "trigger one"
confidence: 0.7
---
Content one.

---
id: second-instinct
trigger: "trigger two"
confidence: 0.8
---
Content two.
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'first-instinct')
        self.assertEqual(result[1]['id'], 'second-instinct')

    def test_parse_instinct_without_frontmatter(self):
        """Test that content without proper frontmatter is ignored."""
        content = '''This is just content without frontmatter.'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 0)

    def test_parse_instinct_missing_id(self):
        """Test that instincts without id are filtered out."""
        content = '''---
trigger: "no id here"
confidence: 0.5
---
Some content.
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 0)

    def test_parse_instinct_default_confidence(self):
        """Test that missing confidence doesn't cause errors."""
        content = '''---
id: no-confidence
trigger: "testing"
---
Content.
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 1)
        # Default confidence should be 0.5 when not specified
        self.assertNotIn('confidence', result[0])

    def test_parse_instinct_quoted_values(self):
        """Test parsing values with different quote styles."""
        content = '''---
id: quoted-test
trigger: "double quoted"
domain: 'single quoted'
confidence: 0.9
---
Content.
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['trigger'], 'double quoted')
        self.assertEqual(result[0]['domain'], 'single quoted')

    def test_parse_empty_content(self):
        """Test parsing instinct with empty content."""
        content = '''---
id: empty-content
trigger: "trigger"
---
'''
        result = parse_instinct_file(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['content'].strip(), '')


class TestLoadAllInstincts(unittest.TestCase):
    """Tests for load_all_instincts function."""

    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.personal_dir = Path(self.temp_dir) / 'personal'
        self.inherited_dir = Path(self.temp_dir) / 'inherited'
        self.personal_dir.mkdir(parents=True)
        self.inherited_dir.mkdir(parents=True)

        # Patch the directories in instinct_cli
        import instinct_cli
        self._original_personal = instinct_cli.PERSONAL_DIR
        self._original_inherited = instinct_cli.INHERITED_DIR
        instinct_cli.PERSONAL_DIR = self.personal_dir
        instinct_cli.INHERITED_DIR = self.inherited_dir

    def tearDown(self):
        """Clean up temporary directories."""
        import instinct_cli
        instinct_cli.PERSONAL_DIR = self._original_personal
        instinct_cli.INHERITED_DIR = self._original_inherited
        shutil.rmtree(self.temp_dir)

    def test_load_from_yaml_file(self):
        """Test loading instincts from .yaml file."""
        yaml_content = '''---
id: yaml-instinct
trigger: "yaml trigger"
confidence: 0.75
domain: yaml-test
---
# YAML Instinct
Content here.
'''
        (self.personal_dir / 'test.yaml').write_text(yaml_content)
        result = load_all_instincts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'yaml-instinct')
        self.assertEqual(result[0]['_source_type'], 'personal')

    def test_load_from_yml_file(self):
        """Test loading instincts from .yml file."""
        yml_content = '''---
id: yml-instinct
trigger: "yml trigger"
confidence: 0.8
---
Content.
'''
        (self.personal_dir / 'test.yml').write_text(yml_content)
        result = load_all_instincts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'yml-instinct')

    def test_load_from_md_file(self):
        """Test loading instincts from .md file."""
        md_content = '''---
id: md-instinct
trigger: "md trigger"
confidence: 0.9
---
Content.
'''
        (self.personal_dir / 'test.md').write_text(md_content)
        result = load_all_instincts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'md-instinct')

    def test_load_from_multiple_directories(self):
        """Test loading from both personal and inherited directories."""
        personal_content = '''---
id: personal-instinct
trigger: "personal"
confidence: 0.7
---
Personal content.
'''
        inherited_content = '''---
id: inherited-instinct
trigger: "inherited"
confidence: 0.8
---
Inherited content.
'''
        (self.personal_dir / 'personal.yaml').write_text(personal_content)
        (self.inherited_dir / 'inherited.yaml').write_text(inherited_content)

        result = load_all_instincts()
        self.assertEqual(len(result), 2)

        ids = [i['id'] for i in result]
        self.assertIn('personal-instinct', ids)
        self.assertIn('inherited-instinct', ids)

        # Check source types
        personal = next(i for i in result if i['id'] == 'personal-instinct')
        inherited = next(i for i in result if i['id'] == 'inherited-instinct')
        self.assertEqual(personal['_source_type'], 'personal')
        self.assertEqual(inherited['_source_type'], 'inherited')

    def test_load_empty_directories(self):
        """Test loading from empty directories."""
        result = load_all_instincts()
        self.assertEqual(len(result), 0)

    def test_load_handles_invalid_files(self):
        """Test that invalid files don't crash the loader."""
        # Create an invalid file
        (self.personal_dir / 'invalid.yaml').write_text('this is not valid yaml: [')
        # Create a valid file
        valid_content = '''---
id: valid-instinct
trigger: "valid"
---
Content.
'''
        (self.personal_dir / 'valid.yaml').write_text(valid_content)

        # Should not crash, should load only valid file
        result = load_all_instincts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'valid-instinct')


class TestCLICommands(unittest.TestCase):
    """Tests for CLI command functionality."""

    def setUp(self):
        """Set up isolated test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
        os.environ['INSTINCT_LEARNING_DATA_DIR'] = self.temp_dir

        # Create directory structure
        (Path(self.temp_dir) / 'instincts' / 'personal').mkdir(parents=True)
        (Path(self.temp_dir) / 'instincts' / 'inherited').mkdir(parents=True)

    def tearDown(self):
        """Clean up test environment."""
        if self.original_env:
            os.environ['INSTINCT_LEARNING_DATA_DIR'] = self.original_env
        else:
            os.environ.pop('INSTINCT_LEARNING_DATA_DIR', None)
        shutil.rmtree(self.temp_dir)

    def _run_cli(self, *args):
        """Helper to run CLI command with isolated environment."""
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py'] + list(args),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=os.environ
        )
        return result

    def test_status_output_format(self):
        """Test that status command produces expected output structure."""
        result = self._run_cli('status')
        # Status should complete without error
        # When no instincts, shows "No instincts found." message
        self.assertTrue(
            'INSTINCT STATUS' in result.stdout or 'No instincts found' in result.stdout,
            f"Unexpected output: {result.stdout}"
        )

    def test_export_no_instincts(self):
        """Test export when no instincts exist."""
        result = self._run_cli('export')
        # Should handle gracefully
        self.assertEqual(result.returncode, 1)

    def test_evolve_insufficient_instincts(self):
        """Test evolve with insufficient instincts."""
        result = self._run_cli('evolve')
        # Should report need for at least 3 instincts
        self.assertIn('at least 3', result.stdout.lower())


class TestImportCommand(unittest.TestCase):
    """Tests for import command functionality."""

    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.import_file = self.temp_dir / 'import.yaml'

        # Set up isolated data directory
        self.data_dir = self.temp_dir / 'data'
        self.original_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
        os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(self.data_dir)

        # Create directory structure
        (self.data_dir / 'instincts' / 'personal').mkdir(parents=True)
        (self.data_dir / 'instincts' / 'inherited').mkdir(parents=True)

        import_content = '''---
id: imported-instinct
trigger: "imported trigger"
confidence: 0.85
domain: imported
---
# Imported Instinct
This was imported.
'''
        self.import_file.write_text(import_content)

    def tearDown(self):
        """Clean up temporary directories."""
        if self.original_env:
            os.environ['INSTINCT_LEARNING_DATA_DIR'] = self.original_env
        else:
            os.environ.pop('INSTINCT_LEARNING_DATA_DIR', None)
        shutil.rmtree(self.temp_dir)

    def _run_cli(self, *args):
        """Helper to run CLI command with isolated environment."""
        result = subprocess.run(
            [sys.executable, 'scripts/instinct_cli.py'] + list(args),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=os.environ
        )
        return result

    def test_import_dry_run(self):
        """Test import with --dry-run flag."""
        result = self._run_cli('import', str(self.import_file), '--dry-run')
        # Should show what would be imported
        self.assertIn('DRY RUN', result.stdout)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
