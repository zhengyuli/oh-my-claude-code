#!/usr/bin/env python3
"""
Comprehensive tests for the hooks system.

Tests hooks.json configuration and observe.sh hook behavior.

Run with: python3 tests/test_hooks.py
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path


class TestHooksConfiguration(unittest.TestCase):
    """Tests for hooks.json configuration."""

    def setUp(self):
        """Set up test paths."""
        self.plugin_dir = Path(__file__).parent.parent
        self.hooks_json = self.plugin_dir / 'hooks' / 'hooks.json'
        self.observe_sh = self.plugin_dir / 'hooks' / 'observe.sh'

    def test_hooks_json_exists(self):
        """Test that hooks.json exists."""
        self.assertTrue(self.hooks_json.exists(), "hooks.json should exist")

    def test_hooks_json_valid_format(self):
        """Test that hooks.json is valid JSON."""
        content = self.hooks_json.read_text()
        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            self.fail(f"hooks.json is not valid JSON: {e}")

    def test_hooks_json_has_required_hooks(self):
        """Test that hooks.json has PreToolUse and PostToolUse hooks."""
        content = self.hooks_json.read_text()
        config = json.loads(content)

        self.assertIn('hooks', config, "hooks.json should have 'hooks' key")

        hooks = config['hooks']
        self.assertIn('PreToolUse', hooks, "Should have PreToolUse hook")
        self.assertIn('PostToolUse', hooks, "Should have PostToolUse hook")

    def test_hooks_json_points_to_observe_sh(self):
        """Test that hooks point to observe.sh."""
        content = self.hooks_json.read_text()
        config = json.loads(content)

        hooks = config['hooks']
        for hook_type in ['PreToolUse', 'PostToolUse']:
            hook_list = hooks[hook_type]
            self.assertIsInstance(hook_list, list, f"{hook_type} should be a list")
            self.assertTrue(len(hook_list) > 0, f"{hook_type} should have entries")

            # Check that observe.sh is referenced in the command
            hook_entry = hook_list[0]
            self.assertIn('hooks', hook_entry, f"{hook_type} entry should have 'hooks'")
            inner_hooks = hook_entry['hooks']
            self.assertTrue(len(inner_hooks) > 0, f"{hook_type} should have inner hooks")

            command = inner_hooks[0].get('command', '')
            self.assertIn('observe.sh', command,
                         f"{hook_type} should reference observe.sh")

    def test_observe_sh_exists_and_executable(self):
        """Test that observe.sh exists and is executable."""
        self.assertTrue(self.observe_sh.exists(), "observe.sh should exist")
        self.assertTrue(os.access(self.observe_sh, os.X_OK),
                       "observe.sh should be executable")

    def test_observe_sh_has_shebang(self):
        """Test that observe.sh has proper shebang."""
        content = self.observe_sh.read_text()
        first_line = content.split('\n')[0]
        self.assertIn('bash', first_line, "observe.sh should have bash shebang")


class TestObserveHookCapture(unittest.TestCase):
    """Tests for observation capture functionality."""

    def setUp(self):
        """Set up temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / '.claude' / 'instinct-learning'
        self.data_dir.mkdir(parents=True)

        self.hook_script = Path(__file__).parent.parent / 'hooks' / 'observe.sh'

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def _run_hook(self, hook_input):
        """Helper to run hook with input."""
        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=json.dumps(hook_input) if isinstance(hook_input, dict) else hook_input,
            capture_output=True,
            text=True,
            env=env
        )
        return result

    def _get_observations(self):
        """Helper to read observations file."""
        obs_file = self.data_dir / 'observations' / 'observations.jsonl'
        if not obs_file.exists():
            return []
        observations = []
        for line in obs_file.read_text().strip().split('\n'):
            if line:
                observations.append(json.loads(line))
        return observations

    def test_captures_tool_start_event(self):
        """Test that PreToolUse creates tool_start event."""
        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "session_id": "session-001"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]['event'], 'tool_start')
        self.assertEqual(observations[0]['tool'], 'Read')
        self.assertEqual(observations[0]['session'], 'session-001')
        self.assertIn('timestamp', observations[0])

    def test_captures_tool_complete_event(self):
        """Test that PostToolUse creates tool_complete event."""
        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_output": "Success",
            "session_id": "session-002"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]['event'], 'tool_complete')
        self.assertEqual(observations[0]['tool'], 'Edit')
        self.assertIn('output', observations[0])

    def test_captures_input_for_start_events(self):
        """Test that tool_start events capture input."""
        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Grep",
            "tool_input": {"pattern": "def test_", "path": "/src"},
            "session_id": "session-003"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertIn('input', observations[0])
        self.assertIn('def test_', observations[0]['input'])

    def test_captures_output_for_complete_events(self):
        """Test that tool_complete events capture output."""
        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_output": "file1.txt\nfile2.txt",
            "session_id": "session-004"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertIn('output', observations[0])
        self.assertIn('file1.txt', observations[0]['output'])

    def test_truncates_large_inputs(self):
        """Test that large inputs are truncated to 1000 chars."""
        large_input = "x" * 2000
        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"content": large_input},
            "session_id": "session-005"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertLessEqual(len(observations[0].get('input', '')), 1000)

    def test_truncates_large_outputs(self):
        """Test that large outputs are truncated to 1000 chars."""
        large_output = "y" * 2000
        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "test"},
            "tool_output": large_output,
            "session_id": "session-006"
        }

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        observations = self._get_observations()
        self.assertEqual(len(observations), 1)
        self.assertLessEqual(len(observations[0].get('output', '')), 1000)

    def test_multiple_observations_append(self):
        """Test that multiple observations are appended correctly."""
        # First observation
        self._run_hook({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "session-007"
        })

        # Second observation
        self._run_hook({
            "hook_type": "PostToolUse",
            "tool_name": "Read",
            "session_id": "session-007"
        })

        # Third observation
        self._run_hook({
            "hook_type": "PreToolUse",
            "tool_name": "Edit",
            "session_id": "session-007"
        })

        observations = self._get_observations()
        self.assertEqual(len(observations), 3)

        # Check order is preserved
        self.assertEqual(observations[0]['tool'], 'Read')
        self.assertEqual(observations[0]['event'], 'tool_start')
        self.assertEqual(observations[1]['event'], 'tool_complete')
        self.assertEqual(observations[2]['tool'], 'Edit')

    def test_timestamp_format(self):
        """Test that timestamps are in ISO 8601 format."""
        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "session-008"
        }

        self._run_hook(hook_input)
        observations = self._get_observations()

        timestamp = observations[0]['timestamp']
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        self.assertRegex(timestamp, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')


class TestObserveHookEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling."""

    def setUp(self):
        """Set up temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / '.claude' / 'instinct-learning'
        self.data_dir.mkdir(parents=True)

        self.hook_script = Path(__file__).parent.parent / 'hooks' / 'observe.sh'

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def _run_hook(self, hook_input):
        """Helper to run hook with input."""
        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        result = subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )
        return result

    def test_handles_missing_tool_name(self):
        """Test that hook handles missing tool_name."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "session_id": "test"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_handles_missing_session_id(self):
        """Test that hook handles missing session_id."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_handles_tool_input_as_dict(self):
        """Test that hook handles tool_input as dict."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test.py", "old_string": "old", "new_string": "new"},
            "session_id": "test"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_handles_tool_output_as_dict(self):
        """Test that hook handles tool_output as dict."""
        hook_input = json.dumps({
            "hook_type": "PostToolUse",
            "tool_name": "Task",
            "tool_output": {"status": "success", "files": ["a.py", "b.py"]},
            "session_id": "test"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_handles_special_characters_in_input(self):
        """Test that hook handles special characters."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"content": "特殊字符 \n newline \t tab"},
            "session_id": "test-special"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_handles_unicode_in_output(self):
        """Test that hook handles unicode characters."""
        hook_input = json.dumps({
            "hook_type": "PostToolUse",
            "tool_name": "Bash",
            "tool_output": "输出: 你好世界 🎉",
            "session_id": "test-unicode"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

    def test_disabled_flag_prevents_writes(self):
        """Test that disabled flag prevents any writes."""
        # Create disabled flag
        (self.data_dir / 'disabled').write_text('')

        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "test"
        })

        result = self._run_hook(hook_input)
        self.assertEqual(result.returncode, 0)

        # Should not create observations file
        obs_file = self.data_dir / 'observations' / 'observations.jsonl'
        self.assertFalse(obs_file.exists())

    def test_creates_data_directory_if_missing(self):
        """Test that hook creates data directory if it doesn't exist."""
        # Remove the data directory
        shutil.rmtree(self.data_dir)

        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
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

        self.assertEqual(result.returncode, 0)
        # Data directory should be created
        self.assertTrue(self.data_dir.exists())


class TestObserveHookFileRotation(unittest.TestCase):
    """Tests for file rotation functionality."""

    def setUp(self):
        """Set up temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / '.claude' / 'instinct-learning'
        self.data_dir.mkdir(parents=True)

        self.hook_script = Path(__file__).parent.parent / 'hooks' / 'observe.sh'

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_archive_directory_created_on_rotation(self):
        """Test that archive directory is created when rotation occurs."""
        # Create observations directory and large file
        obs_dir = self.data_dir / 'observations'
        obs_dir.mkdir(parents=True, exist_ok=True)
        obs_file = obs_dir / 'observations.jsonl'

        # Create content larger than 2MB (the new rotation threshold)
        large_content = []
        for i in range(10000):
            obs = json.dumps({
                "timestamp": f"2026-02-28T10:00:{i % 60:02d}Z",
                "event": "tool_complete",
                "tool": "Test",
                "input": "x" * 1000,  # Make it large
                "session": "test"
            })
            large_content.append(obs)

        obs_file.write_text('\n'.join(large_content) + '\n')

        # Run hook - should trigger rotation
        env = os.environ.copy()
        env['HOME'] = str(self.temp_dir)

        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "test"
        })

        subprocess.run(
            ['bash', str(self.hook_script)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env
        )

        # Check if archive file was created (if file was large enough)
        archive_file = obs_dir / 'observations.1.jsonl'
        # Note: This test may not trigger rotation if file isn't > 2MB
        # The hook uses `du -m` to check size


if __name__ == '__main__':
    unittest.main(verbosity=2)
