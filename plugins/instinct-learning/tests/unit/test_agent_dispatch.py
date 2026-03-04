"""Test agent dispatch behavior."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestAgentDispatch:
    """Test agent dispatching logic."""

    @pytest.mark.parametrize("agent_type,expected_format", [
        ('analyzer', 'instinct-learning:analyzer'),
        ('evolver', 'instinct-learning:evolver'),
    ])
    def test_subagent_type_format(self, agent_type, expected_format):
        """Test agent subagent_type follows correct format."""
        assert ':' in expected_format
        assert expected_format.startswith('instinct-learning:')

    def test_agent_names_are_kebab_case(self):
        """Test that agent names use kebab-case format."""
        for agent_name in ['analyzer', 'evolver']:
            assert ' ' not in agent_name
            assert '_' not in agent_name

    @pytest.mark.parametrize("agent,expected_model", [
        ('analyzer', 'haiku'),
        ('evolver', 'sonnet'),
    ])
    def test_agent_uses_correct_model(self, agent, expected_model):
        """Test that agents use the correct model."""
        agent_file = Path(__file__).parent.parent.parent / "agents" / f"{agent}.md"
        content = agent_file.read_text()
        assert f'model: {expected_model}' in content
        assert 'description' in content
        assert 'tools' in content

    def test_agents_have_required_tools(self):
        """Test that agents have Read, Bash, Write tools."""
        for agent_name in ['analyzer', 'evolver']:
            agent_file = Path(__file__).parent.parent.parent / "agents" / f"{agent_name}.md"
            content = agent_file.read_text()
            assert 'Read' in content
            assert 'Bash' in content
            assert 'Write' in content


@pytest.mark.unit
class TestAgentFileStructure:
    """Test agent file structure and metadata."""

    @pytest.mark.parametrize("agent", ['analyzer', 'evolver'])
    def test_agent_has_required_sections(self, agent):
        """Test agent has required sections."""
        agent_file = Path(__file__).parent.parent.parent / "agents" / f"{agent}.md"
        content = agent_file.read_text()
        assert '## Task' in content
        assert '## Process' in content
        assert '## Constraints' in content
        assert '## Error Handling' in content
        assert '### 0. Set Data Directory' in content
        assert 'INSTINCT_LEARNING_DATA_DIR' in content
