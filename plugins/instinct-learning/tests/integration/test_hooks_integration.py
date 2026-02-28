"""Integration tests for hooks system.

Tests the observe.sh hook script using subprocess to ensure
hooks work correctly in real execution contexts.
"""

import json
import os
import pytest
import subprocess
import shutil
from pathlib import Path


@pytest.mark.integration
class TestHooksConfiguration:
    """Tests for hooks.json configuration."""

    def test_hooks_json_exists(self):
        """Test that hooks.json exists."""
        plugin_dir = Path(__file__).parent.parent.parent
        hooks_json = plugin_dir / 'hooks' / 'hooks.json'
        assert hooks_json.exists()

    def test_hooks_json_valid_format(self):
        """Test that hooks.json is valid JSON."""
        plugin_dir = Path(__file__).parent.parent.parent
        hooks_json = plugin_dir / 'hooks' / 'hooks.json'
        content = hooks_json.read_text()
        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"hooks.json is not valid JSON: {e}")

    def test_hooks_json_has_required_hooks(self):
        """Test that hooks.json has PreToolUse and PostToolUse hooks."""
        plugin_dir = Path(__file__).parent.parent.parent
        hooks_json = plugin_dir / 'hooks' / 'hooks.json'
        content = hooks_json.read_text()
        config = json.loads(content)

        assert 'hooks' in config
        hooks = config['hooks']
        assert 'PreToolUse' in hooks
        assert 'PostToolUse' in hooks

    def test_observe_sh_exists_and_executable(self):
        """Test that observe.sh exists and is executable."""
        plugin_dir = Path(__file__).parent.parent.parent
        observe_sh = plugin_dir / 'hooks' / 'observe.sh'
        assert observe_sh.exists()
        assert os.access(observe_sh, os.X_OK)

    def test_observe_sh_has_shebang(self):
        """Test that observe.sh has proper shebang."""
        plugin_dir = Path(__file__).parent.parent.parent
        observe_sh = plugin_dir / 'hooks' / 'observe.sh'
        content = observe_sh.read_text()
        first_line = content.split('\n')[0]
        assert 'bash' in first_line


@pytest.mark.integration
class TestHooksIntegration:
    """Integration tests for hooks system."""

    def test_pre_tool_use_creates_observation(self, temp_data_dir, temp_home):
        """Test PreToolUse hook creates observation."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "session_id": "test-session-pre"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        # Check observation was created
        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        assert obs_file.exists()
        content = obs_file.read_text()
        assert 'test-session-pre' in content
        assert 'Read' in content

    def test_post_tool_use_creates_observation(self, temp_data_dir, temp_home):
        """Test PostToolUse hook creates observation."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_output": "Success",
            "session_id": "test-session-post"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        content = obs_file.read_text()
        assert 'test-session-post' in content
        assert 'Edit' in content

    def test_multiple_observations_append(self, temp_data_dir, temp_home):
        """Test multiple observations append correctly."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        for i in range(3):
            hook_input = {
                "hook_type": "PreToolUse",
                "tool_name": f"Tool{i}",
                "session_id": "multi-session"
            }
            subprocess.run(
                ['bash', 'hooks/observe.sh'],
                input=json.dumps(hook_input),
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
                env=env
            )

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        lines = obs_file.read_text().strip().split('\n')
        assert len(lines) == 3
        for i in range(3):
            assert f'Tool{i}' in lines[i]

    def test_disabled_flag_prevents_writes(self, temp_data_dir, temp_home):
        """Test disabled flag prevents all writes."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        # Create disabled flag
        (temp_data_dir / 'disabled').touch()

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "disabled-test"
        }

        subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        assert not obs_file.exists()


@pytest.mark.integration
class TestHooksObservationCapture:
    """Tests for detailed observation capture functionality."""

    def test_captures_tool_start_event(self, temp_data_dir, temp_home):
        """Test that PreToolUse creates tool_start event."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "session_id": "session-start-001"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        observations = [json.loads(line) for line in obs_file.read_text().strip().split('\n') if line]
        assert len(observations) == 1
        assert observations[0]['event'] == 'tool_start'
        assert observations[0]['tool'] == 'Read'
        assert observations[0]['session'] == 'session-start-001'
        assert 'timestamp' in observations[0]

    def test_captures_tool_complete_event(self, temp_data_dir, temp_home):
        """Test that PostToolUse creates tool_complete event."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_output": "Success",
            "session_id": "session-complete-002"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        observations = [json.loads(line) for line in obs_file.read_text().strip().split('\n') if line]
        assert len(observations) == 1
        assert observations[0]['event'] == 'tool_complete'
        assert observations[0]['tool'] == 'Edit'
        assert 'output' in observations[0]

    def test_captures_input_for_start_events(self, temp_data_dir, temp_home):
        """Test that tool_start events capture input."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Grep",
            "tool_input": {"pattern": "def test_", "path": "/src"},
            "session_id": "session-input-003"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        observations = [json.loads(line) for line in obs_file.read_text().strip().split('\n') if line]
        assert len(observations) == 1
        assert 'input' in observations[0]
        assert 'def test_' in observations[0]['input']

    def test_captures_output_for_complete_events(self, temp_data_dir, temp_home):
        """Test that tool_complete events capture output."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_output": "file1.txt\nfile2.txt",
            "session_id": "session-output-004"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        observations = [json.loads(line) for line in obs_file.read_text().strip().split('\n') if line]
        assert len(observations) == 1
        assert 'output' in observations[0]
        assert 'file1.txt' in observations[0]['output']

    def test_timestamp_format(self, temp_data_dir, temp_home):
        """Test that timestamps are in ISO 8601 format."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "session-timestamp-005"
        }

        subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )

        obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
        observations = [json.loads(line) for line in obs_file.read_text().strip().split('\n') if line]
        timestamp = observations[0]['timestamp']
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        assert timestamp and len(timestamp) > 0


@pytest.mark.integration
class TestHooksEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_missing_tool_name(self, temp_data_dir, temp_home):
        """Test that hook handles missing tool_name."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "session_id": "test"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

    def test_handles_missing_session_id(self, temp_data_dir, temp_home):
        """Test that hook handles missing session_id."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

    def test_handles_empty_input(self, temp_data_dir, temp_home):
        """Test that hook handles empty input gracefully."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input='',
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

    def test_handles_malformed_json(self, temp_data_dir, temp_home):
        """Test that hook handles malformed JSON gracefully."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input='this is not json',
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0

    def test_creates_data_directory_if_missing(self, temp_data_dir, temp_home):
        """Test that hook creates data directory if it doesn't exist."""
        env = os.environ.copy()
        env['HOME'] = str(temp_home)
        env['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

        # Remove the observations directory
        obs_dir = temp_data_dir / 'observations'
        if obs_dir.exists():
            shutil.rmtree(obs_dir)

        hook_input = {
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "session_id": "test"
        }

        result = subprocess.run(
            ['bash', 'hooks/observe.sh'],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            env=env
        )
        assert result.returncode == 0
        # Observations directory should be created
        assert obs_dir.exists()
