#!/usr/bin/env python3
"""
Tests for observe.sh hook script.

Run with: python3 tests/test_observe_sh.py
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path


class TestObserveHook(unittest.TestCase):
    """Tests for the observe.sh hook script."""

    def setUp(self):
        """Set up temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / '.claude' / 'instinct-learning'
        self.data_dir.mkdir(parents=True)

        self.hook_script = Path(__file__).parent.parent / 'hooks' / 'observe.sh'

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_hook_exists_and_executable(self):
        """Test that observe.sh exists and is executable."""
        self.assertTrue(self.hook_script.exists(), "observe.sh should exist")
        # Check if executable
        result = subprocess.run(
            ['test', '-x', str(self.hook_script)],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0, "observe.sh should be executable")

    def test_hook_handles_pre_tool_use(self):
        """Test hook handles PreToolUse event."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "session_id": "test-session-123"
        })

        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        # Hook should complete successfully
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

    def test_hook_handles_post_tool_use(self):
        """Test hook handles PostToolUse event."""
        hook_input = json.dumps({
            "hook_type": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_output": "File edited successfully",
            "session_id": "test-session-456"
        })

        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        # Hook should complete successfully
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

    def test_hook_creates_observations_file(self):
        """Test that hook creates observations.jsonl file."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "session_id": "test-session-789"
        })

        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        # Check observations file was created
        obs_file = self.data_dir / 'observations.jsonl'
        self.assertTrue(obs_file.exists(), f"observations.jsonl should be created at {obs_file}")

    def test_hook_writes_valid_json(self):
        """Test that hook writes valid JSON to observations file."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Grep",
            "tool_input": {"pattern": "test"},
            "session_id": "test-session-abc"
        })

        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        obs_file = self.data_dir / 'observations.jsonl'
        if obs_file.exists():
            content = obs_file.read_text()
            lines = [l for l in content.strip().split('\n') if l]
            for line in lines:
                # Each line should be valid JSON
                try:
                    data = json.loads(line)
                    self.assertIn('timestamp', data)
                    self.assertIn('event', data)
                    self.assertIn('tool', data)
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in observations: {line}\nError: {e}")

    def test_hook_handles_empty_input(self):
        """Test that hook handles empty input gracefully."""
        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input='',
            capture_output=True,
            text=True,
            env=env
        )

        # Should not crash
        self.assertEqual(result.returncode, 0)

    def test_hook_handles_malformed_json(self):
        """Test that hook handles malformed JSON gracefully."""
        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input='this is not json',
            capture_output=True,
            text=True,
            env=env
        )

        # Should not crash
        self.assertEqual(result.returncode, 0)

    def test_hook_respects_disabled_flag(self):
        """Test that hook respects the disabled flag."""
        # Create disabled flag
        (self.data_dir / 'disabled').touch()

        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Test",
            "session_id": "test"
        })

        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        # Should exit without writing
        obs_file = self.data_dir / 'observations.jsonl'
        self.assertFalse(obs_file.exists(), "Should not create observations when disabled")


if __name__ == '__main__':
    unittest.main(verbosity=2)
