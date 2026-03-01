"""Simple unit tests for observe.sh hook script.

This module tests basic hook script functionality without requiring
full subprocess execution.
"""

import pytest
import os
from pathlib import Path

# Get plugin root directory (parent of tests directory)
PLUGIN_ROOT = Path(__file__).parent.parent.parent


@pytest.mark.unit
class TestObserveHookScript:
    """Test observe.sh hook script properties."""

    @pytest.fixture
    def hook_script_path(self):
        """Path to the observe.sh script."""
        return PLUGIN_ROOT / 'hooks' / 'observe.sh'

    def test_hook_script_exists(self, hook_script_path):
        """Test that the hook script file exists."""
        assert hook_script_path.exists()

    def test_hook_script_is_executable(self, hook_script_path):
        """Test that the hook script has execute permissions."""
        # On Windows, this test may not apply
        if os.name != 'nt':
            assert os.access(hook_script_path, os.X_OK) or hook_script_path.stat().st_mode & 0o111 != 0

    def test_hook_script_has_shebang(self, hook_script_path):
        """Test that the hook script starts with proper shebang."""
        content = hook_script_path.read_text()
        assert content.startswith('#!/bin/bash')

    def test_hook_script_has_lock_file_support(self, hook_script_path):
        """Test that the hook script includes lock-based locking (flock or mkdir)."""
        content = hook_script_path.read_text()
        # Check for either flock-based or mkdir-based locking
        has_flock = 'LOCK_FILE' in content or 'flock' in content
        has_mkdir_lock = 'LOCK_DIR' in content and 'mkdir' in content and '.lockdir' in content
        assert has_flock or has_mkdir_lock

    def test_hook_script_has_env_var_support(self, hook_script_path):
        """Test that the hook script supports INSTINCT_LEARNING_DATA_DIR."""
        content = hook_script_path.read_text()
        assert 'INSTINCT_LEARNING_DATA_DIR' in content

    def test_hook_script_has_rotation_logic(self, hook_script_path):
        """Test that the hook script includes file rotation logic."""
        content = hook_script_path.read_text()
        assert 'MAX_FILE_SIZE' in content or 'MAX_ARCHIVE' in content or 'rotation' in content.lower()

    def test_hook_script_has_json_parsing(self, hook_script_path):
        """Test that the hook script includes JSON parsing."""
        content = hook_script_path.read_text()
        assert 'python3' in content or 'json' in content

    def test_hook_script_has_disabled_flag_check(self, hook_script_path):
        """Test that the hook script checks for disabled flag."""
        content = hook_script_path.read_text()
        assert 'disabled' in content.lower()


@pytest.mark.unit
class TestAgentDispatchTests:
    """Test agent dispatch configuration."""

    def test_analyzer_agent_file_exists(self):
        """Test that analyzer agent file exists."""
        analyzer_path = PLUGIN_ROOT / 'agents' / 'analyzer.md'
        assert analyzer_path.exists()

    def test_evolver_agent_file_exists(self):
        """Test that evolver agent file exists."""
        evolver_path = PLUGIN_ROOT / 'agents' / 'evolver.md'
        assert evolver_path.exists()

    def test_analyzer_agent_uses_haiku(self):
        """Test that analyzer agent uses haiku model."""
        analyzer_path = PLUGIN_ROOT / 'agents' / 'analyzer.md'
        content = analyzer_path.read_text()
        assert 'model: haiku' in content

    def test_evolver_agent_uses_sonnet(self):
        """Test that evolver agent uses sonnet model."""
        evolver_path = PLUGIN_ROOT / 'agents' / 'evolver.md'
        content = evolver_path.read_text()
        assert 'model: sonnet' in content

    def test_agents_have_env_var_support(self):
        """Test that agent files support INSTINCT_LEARNING_DATA_DIR."""
        analyzer_path = PLUGIN_ROOT / 'agents' / 'analyzer.md'
        evolver_path = PLUGIN_ROOT / 'agents' / 'evolver.md'

        analyzer_content = analyzer_path.read_text()
        evolver_content = evolver_path.read_text()

        assert 'INSTINCT_LEARNING_DATA_DIR' in analyzer_content
        assert 'INSTINCT_LEARNING_DATA_DIR' in evolver_content
