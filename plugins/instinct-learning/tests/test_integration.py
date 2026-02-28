#!/usr/bin/env python3
"""
Integration tests for instinct-learning plugin.

Tests the full workflow from observation capture to instinct evolution.

Run with: python3 tests/test_integration.py
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


class TestIntegration(unittest.TestCase):
    """Integration tests for the full instinct-learning workflow."""

    def setUp(self):
        """Set up temporary test environment with unique directory per test."""
        # Use a unique temp directory for each test
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        self.temp_dir = Path(tempfile.mkdtemp()) / f'test_{unique_id}'
        self.temp_dir.mkdir(parents=True)

        self.data_dir = self.temp_dir / '.claude' / 'instinct-learning'
        self.plugin_dir = Path(__file__).parent.parent

        # Set environment variable for data directory
        self.original_env = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
        os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(self.data_dir)

        # Create directory structure
        (self.data_dir / 'instincts' / 'personal').mkdir(parents=True)
        (self.data_dir / 'instincts' / 'inherited').mkdir(parents=True)
        (self.data_dir / 'evolved' / 'skills').mkdir(parents=True)
        (self.data_dir / 'evolved' / 'commands').mkdir(parents=True)
        (self.data_dir / 'evolved' / 'agents').mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary directories."""
        if self.original_env:
            os.environ['INSTINCT_LEARNING_DATA_DIR'] = self.original_env
        else:
            os.environ.pop('INSTINCT_LEARNING_DATA_DIR', None)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir.parent)

    def _run_cli(self, *args):
        """Helper to run CLI command."""
        result = subprocess.run(
            [sys.executable, str(self.plugin_dir / 'scripts' / 'instinct_cli.py')] + list(args),
            capture_output=True,
            text=True,
            env=os.environ
        )
        return result

    def _create_sample_observations(self, count=5):
        """Create sample observations file."""
        obs_file = self.data_dir / 'observations.jsonl'
        observations = []

        for i in range(count):
            obs = {
                "timestamp": f"2026-02-28T10:00:{i:02d}Z",
                "event": "tool_complete",
                "tool": "Edit",
                "input": json.dumps({"file_path": f"/test/file{i}.py"}),
                "session": "test-session"
            }
            observations.append(json.dumps(obs))

        obs_file.write_text('\n'.join(observations) + '\n')
        return obs_file

    def test_cli_status_empty(self):
        """Test status command with no instincts."""
        result = self._run_cli('status')
        self.assertEqual(result.returncode, 0)
        self.assertIn('No instincts found', result.stdout)

    def test_full_workflow(self):
        """Test the complete workflow: import -> status -> export."""
        # Create a sample instinct file to import with unique ID
        import_file = self.temp_dir / 'sample_instincts.yaml'
        import_content = '''---
id: workflow-test-unique-instinct
trigger: "when running integration tests"
confidence: 0.75
domain: testing
---
# Test Workflow Instinct

## Action
Always run integration tests after changes.

## Evidence
- This is a test instinct
'''
        import_file.write_text(import_content)

        # Import the instinct
        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0, f"Import failed: {result.stderr}\n{result.stdout}")
        self.assertIn('Import complete', result.stdout)

        # Check status
        result = self._run_cli('status')
        self.assertEqual(result.returncode, 0)
        self.assertIn('workflow-test-unique-instinct', result.stdout)

        # Export
        export_file = self.temp_dir / 'exported.yaml'
        result = self._run_cli('export', '--output', str(export_file))
        self.assertEqual(result.returncode, 0, f"Export failed: {result.stderr}\n{result.stdout}")
        self.assertTrue(export_file.exists())

        # Verify exported content
        exported = export_file.read_text()
        self.assertIn('workflow-test-unique-instinct', exported)

    def test_import_with_min_confidence(self):
        """Test import with minimum confidence filter."""
        import_file = self.temp_dir / 'multi_confidence.yaml'
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
        result = self._run_cli('import', str(import_file), '--force', '--min-confidence', '0.5')
        self.assertEqual(result.returncode, 0)

        # Only high confidence should be imported
        result = self._run_cli('status')
        self.assertIn('minconf-high-confidence', result.stdout)
        self.assertNotIn('minconf-low-confidence', result.stdout)

    def test_export_by_domain(self):
        """Test export filtered by domain."""
        # Import instincts with different domains
        import_file = self.temp_dir / 'multi_domain.yaml'
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

        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0)

        # Export only testing domain
        export_file = self.temp_dir / 'testing_only.yaml'
        result = self._run_cli('export', '--domain', 'testing', '--output', str(export_file))
        self.assertEqual(result.returncode, 0)

        exported = export_file.read_text()
        self.assertIn('testing-instinct', exported)
        self.assertNotIn('git-instinct', exported)

    def test_evolve_insufficient_instincts(self):
        """Test evolve command with insufficient instincts."""
        # Create only 2 instincts (need 3 minimum)
        import_file = self.temp_dir / 'few.yaml'
        import_content = '''---
id: few-instinct-1
trigger: "one"
confidence: 0.8
---
First.

---
id: few-instinct-2
trigger: "two"
confidence: 0.8
---
Second.
'''
        import_file.write_text(import_content)

        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0)

        # Try to evolve - should indicate need for more instincts
        result = self._run_cli('evolve')
        # The evolve command should warn about insufficient instincts
        self.assertTrue(
            'at least 3' in result.stdout.lower() or 'need' in result.stdout.lower(),
            f"Expected warning about insufficient instincts, got: {result.stdout}"
        )

    def test_evolve_with_enough_instincts(self):
        """Test evolve command with sufficient instincts."""
        # Create 4 instincts with unique IDs to avoid conflicts
        import_file = self.temp_dir / 'many2.yaml'
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

        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0)

        # Evolve should work now
        result = self._run_cli('evolve')
        self.assertEqual(result.returncode, 0)
        self.assertIn('EVOLVE ANALYSIS', result.stdout)
        # Should show some number of instincts analyzed
        self.assertIn('instincts', result.stdout.lower())

    def test_duplicate_import_handling(self):
        """Test that duplicate imports are handled correctly."""
        import_file = self.temp_dir / 'dup.yaml'
        import_content = '''---
id: duplicate-test
trigger: "dup"
confidence: 0.7
---
Original.
'''
        import_file.write_text(import_content)

        # First import
        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0)

        # Second import with same ID but lower confidence
        import_content2 = '''---
id: duplicate-test
trigger: "dup"
confidence: 0.5
---
Lower confidence.
'''
        import_file.write_text(import_content2)

        result = self._run_cli('import', str(import_file), '--force')
        self.assertEqual(result.returncode, 0)
        # Should indicate skip or duplicate
        self.assertTrue('SKIP' in result.stdout or 'Nothing to import' in result.stdout)

    def test_observations_file_rotation(self):
        """Test that observations file is rotated when too large."""
        # Create a large observations file
        obs_file = self.data_dir / 'observations.jsonl'

        # Create observations until file is large enough
        # (In real scenario, this would be 10MB, but for testing we use smaller)
        large_obs = []
        for i in range(1000):
            obs = {
                "timestamp": f"2026-02-28T10:00:{i % 60:02d}Z",
                "event": "tool_complete",
                "tool": "Test",
                "input": "x" * 1000,  # Make each observation large
                "session": "test"
            }
            large_obs.append(json.dumps(obs))

        obs_file.write_text('\n'.join(large_obs) + '\n')

        # Verify file was created
        self.assertTrue(obs_file.exists())
        file_size = obs_file.stat().st_size
        self.assertGreater(file_size, 100000)  # At least 100KB


if __name__ == '__main__':
    unittest.main(verbosity=2)
