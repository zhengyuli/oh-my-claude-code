"""Pytest configuration and shared fixtures for instinct-learning tests."""

import pytest
import tempfile
import shutil
import json
import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to Python path for imports
scripts_dir = Path(__file__).parent.parent / 'scripts'
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


@pytest.fixture
def temp_data_dir():
    """Temporary data directory isolated for each test.

    Creates a full directory structure:
    - .claude/instinct-learning/instincts/personal/
    - .claude/instinct-learning/instincts/inherited/
    - .claude/instinct-learning/instincts/archived/
    - .claude/instinct-learning/observations/
    """
    temp_dir = Path(tempfile.mkdtemp())
    data_dir = temp_dir / '.claude' / 'instinct-learning'
    data_dir.mkdir(parents=True)
    (data_dir / 'instincts' / 'personal').mkdir(parents=True)
    (data_dir / 'instincts' / 'inherited').mkdir(parents=True)
    (data_dir / 'instincts' / 'archived').mkdir(parents=True)
    (data_dir / 'observations').mkdir(parents=True)
    yield data_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_home(monkeypatch, temp_data_dir):
    """Set HOME to temp directory for hooks testing.

    This fixture sets both HOME and INSTINCT_LEARNING_DATA_DIR
    environment variables to point to the temporary data directory,
    ensuring tests don't affect the user's actual environment.
    """
    home = temp_data_dir.parent.parent
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('INSTINCT_LEARNING_DATA_DIR', str(temp_data_dir))
    return home


@pytest.fixture
def sample_observation():
    """Single sample observation record.

    Returns a dict with typical observation structure including
    timestamp, event type, tool name, input, and session ID.
    """
    return {
        "timestamp": "2026-02-28T10:00:00Z",
        "event": "tool_complete",
        "tool": "Edit",
        "input": '{"file_path": "/test/file.py"}',
        "session": "test-session-001"
    }


@pytest.fixture
def sample_instinct_yaml():
    """Sample instinct in YAML format.

    Returns a string containing a complete instinct definition
    with YAML frontmatter and markdown body.
    """
    return '''---
id: test-instinct
trigger: "when testing code"
confidence: 0.85
domain: testing
source: session-observation
created: "2026-02-28T10:00:00Z"
last_observed: "2026-02-28T10:00:00Z"
evidence_count: 5
---
# Test Instinct

## Action
Run tests before committing.

## Evidence
- Observed 5 times
'''


@pytest.fixture
def mock_observations_file(temp_data_dir, sample_observation):
    """Create a pre-populated observations file.

    Creates observations.jsonl with 5 sample observation records,
    each with a different session ID.
    """
    obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
    for i in range(5):
        obs = sample_observation.copy()
        obs['session'] = f'test-session-{i}'
        with open(obs_file, 'a') as f:
            f.write(json.dumps(obs) + '\n')
    return obs_file
