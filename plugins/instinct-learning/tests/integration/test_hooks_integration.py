"""Integration tests for hooks system.

Tests the observe.sh hook script using subprocess to ensure
hooks work correctly in real execution contexts.
"""

import json
import os
import pytest
import subprocess
from pathlib import Path


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
