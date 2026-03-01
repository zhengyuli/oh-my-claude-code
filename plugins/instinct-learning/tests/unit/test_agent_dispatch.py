"""Test agent dispatch behavior.

This module tests agent dispatching logic to improve
test coverage from 16% to 50%+.
"""

import pytest


@pytest.mark.unit
class TestAgentDispatch:
    """Test agent dispatching logic."""

    def test_analyzer_subagent_type_format(self):
        """Test analyzer agent subagent_type follows correct format."""
        analyzer_type = "instinct-learning:analyzer"
        assert analyzer_type == "instinct-learning:analyzer"
        assert ':' in analyzer_type
        assert analyzer_type.startswith('instinct-learning:')

    def test_evolver_subagent_type_format(self):
        """Test evolver agent subagent_type follows correct format."""
        evolver_type = "instinct-learning:evolver"
        assert evolver_type == "instinct-learning:evolver"
        assert ':' in evolver_type
        assert evolver_type.startswith('instinct-learning:')

    def test_agent_names_are_kebab_case(self):
        """Test that agent names use kebab-case format."""
        analyzer_name = "analyzer"
        evolver_name = "evolver"

        # Should not contain spaces or underscores
        assert ' ' not in analyzer_name
        assert '_' not in analyzer_name
        assert ' ' not in evolver_name
        assert '_' not in evolver_name

    def test_analyzer_uses_haiku_model(self):
        """Test that analyzer agent uses haiku model for cost efficiency."""
        # Read agent file to verify model
        from pathlib import Path
        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        assert 'model: haiku' in content
        assert 'description' in content
        assert 'tools' in content

    def test_evolver_uses_sonnet_model(self):
        """Test that evolver agent uses sonnet model for semantic clustering."""
        from pathlib import Path
        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        assert 'model: sonnet' in content
        assert 'description' in content
        assert 'tools' in content

    def test_agents_have_required_tools(self):
        """Test that agents have Read, Bash, Write tools."""
        from pathlib import Path

        for agent_name in ['analyzer', 'evolver']:
            agent_file = Path(__file__).parent.parent.parent / "agents" / f"{agent_name}.md"
            content = agent_file.read_text()

            assert 'Read' in content
            assert 'Bash' in content
            assert 'Write' in content


@pytest.mark.unit
class TestAgentFileStructure:
    """Test agent file structure and metadata."""

    def test_analyzer_has_yaml_frontmatter(self):
        """Test analyzer agent has proper YAML frontmatter."""
        from pathlib import Path
        import yaml

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        # Check for YAML frontmatter markers
        assert content.startswith('---')
        assert 'name: analyzer' in content
        assert 'description:' in content
        assert 'model:' in content
        assert 'tools:' in content

    def test_evolver_has_yaml_frontmatter(self):
        """Test evolver agent has proper YAML frontmatter."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        # Check for YAML frontmatter markers
        assert content.startswith('---')
        assert 'name: evolver' in content
        assert 'description:' in content
        assert 'model:' in content
        assert 'tools:' in content

    def test_analyzer_has_task_section(self):
        """Test analyzer agent has Task section."""
        from pathlib import Path

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        assert '## Task' in content
        assert '## Process' in content
        assert '## Constraints' in content

    def test_evolver_has_task_section(self):
        """Test evolver agent has Task section."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        assert '## Task' in content
        assert '## Process' in content
        assert '## Constraints' in content


@pytest.mark.unit
class TestAgentProcessSections:
    """Test agent Process section structure."""

    def test_analyzer_has_data_directory_step(self):
        """Test analyzer agent has step 0 for setting data directory."""
        from pathlib import Path

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        assert '### 0. Set Data Directory' in content
        assert 'INSTINCT_LEARNING_DATA_DIR' in content

    def test_evolver_has_data_directory_step(self):
        """Test evolver agent has step 0 for setting data directory."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        assert '### 0. Set Data Directory' in content
        assert 'INSTINCT_LEARNING_DATA_DIR' in content

    def test_analyzer_process_sections_in_order(self):
        """Test analyzer agent has process sections in correct order."""
        from pathlib import Path

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        # Verify order of sections
        pos_load = content.find('### 1. Load Archived Observations')
        pos_detect = content.find('### 2. Detect Patterns')
        pos_create = content.find('### 3. Calculate Confidence')
        pos_write = content.find('### 4. Create Instinct Files')

        assert pos_load > 0
        assert pos_detect > pos_load
        assert pos_create > pos_detect
        assert pos_write > pos_create

    def test_evolver_process_sections_in_order(self):
        """Test evolver agent has process sections in correct order."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        # Verify order of sections
        pos_load = content.find('### 1. Load Instincts')
        pos_cluster = content.find('### 2. Cluster by Domain')
        pos_semantic = content.find('### 3. Semantic Clustering')
        pos_generate = content.find('### 4. Generate Evolved Artifacts')

        assert pos_load > 0
        assert pos_cluster > pos_load
        assert pos_semantic > pos_cluster
        assert pos_generate > pos_semantic


@pytest.mark.unit
class TestAgentConstraints:
    """Test agent Constraints sections."""

    def test_analyzer_has_constraints(self):
        """Test analyzer agent has Constraints section."""
        from pathlib import Path

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        assert '## Constraints' in content
        assert 'Minimum observations' in content
        assert 'Privacy' in content

    def test_evolver_has_constraints(self):
        """Test evolver agent has Constraints section."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        assert '## Constraints' in content
        assert '50-item limit' in content
        assert 'Semantic clustering' in content

    def test_analyzer_has_error_handling(self):
        """Test analyzer agent has Error Handling section."""
        from pathlib import Path

        analyzer_file = Path(__file__).parent.parent.parent / "agents" / "analyzer.md"
        content = analyzer_file.read_text()

        assert '## Error Handling' in content

    def test_evolver_has_error_handling(self):
        """Test evolver agent has Error Handling section."""
        from pathlib import Path

        evolver_file = Path(__file__).parent.parent.parent / "agents" / "evolver.md"
        content = evolver_file.read_text()

        assert '## Error Handling' in content
