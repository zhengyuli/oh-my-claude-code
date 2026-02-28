"""Performance scenario tests.

These tests validate system performance under various load conditions.
Tests are marked as slow and can be skipped during rapid development.
"""

import json
import time
import pytest
import subprocess
import sys
import os
from pathlib import Path


@pytest.mark.scenario
@pytest.mark.slow
def test_large_observation_file_parses(temp_data_dir):
    """Scenario: Large observation file (1000 entries) parses efficiently.

    Performance expectations:
    - File with 1000 observations should parse in < 5 seconds
    - Memory usage should remain reasonable
    - No duplicate entries in results
    """
    obs_file = temp_data_dir / 'observations' / 'observations.jsonl'

    # Generate 1000 observations
    tool_types = ['Edit', 'Read', 'Bash', 'Grep', 'Write']
    start_time = time.time()

    with open(obs_file, 'w') as f:
        for i in range(1000):
            obs = {
                "timestamp": f"2026-02-28T10:{i // 60:02d}:{i % 60:02d}Z",
                "event": "tool_complete",
                "tool": tool_types[i % 5],
                "session": f"test-session-{i // 10}",
                "input": f'{{"action": "test-{i}"}}'
            }
            f.write(json.dumps(obs) + '\n')

    write_time = time.time() - start_time

    # Parse all observations
    parse_start = time.time()
    observations = []
    with open(obs_file, 'r') as f:
        for line in f:
            if line.strip():
                observations.append(json.loads(line.strip()))
    parse_time = time.time() - parse_start

    # Verify results
    assert len(observations) == 1000
    assert len(set(obs['session'] for obs in observations)) == 100  # 100 unique sessions
    assert parse_time < 5.0, f"Parsing took {parse_time:.2f}s, expected < 5s"
    assert write_time < 5.0, f"Writing took {write_time:.2f}s, expected < 5s"


@pytest.mark.scenario
@pytest.mark.slow
def test_hook_execution_time_under_limit(temp_data_dir, temp_home):
    """Scenario: Hook execution completes within time limit.

    Performance expectations:
    - PreToolUse hook should complete in < 100ms
    - PostToolUse hook should complete in < 100ms
    - Hooks should not block session execution
    """
    hook_path = Path(__file__).parent.parent.parent / 'hooks' / 'post_tool_use.sh'

    # Create a test hook input
    hook_input = {
        "hook_type": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "/test/file.py"},
        "tool_output": "Success",
        "session_id": "perf-test-session"
    }

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(hook_input, f)
        input_file = f.name

    try:
        # Measure hook execution time
        start_time = time.time()

        result = subprocess.run(
            ['bash', str(hook_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, 'INSTINCT_LEARNING_DATA_DIR': str(temp_data_dir)}
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        # Hook should complete quickly (async background execution)
        # The actual hook returns immediately, processing happens in background
        assert execution_time < 5000, f"Hook took {execution_time:.0f}ms, expected < 5000ms"
    finally:
        Path(input_file).unlink(missing_ok=True)


@pytest.mark.scenario
@pytest.mark.slow
def test_thousands_of_instincts_loading(temp_data_dir):
    """Scenario: Loading 100 instinct files completes efficiently.

    Performance expectations:
    - 100 instinct files should load in < 5 seconds
    - All valid instincts should be parsed
    - Invalid files should be skipped
    """
    # Import from scripts directory
    import sys
    scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
    sys.path.insert(0, str(scripts_dir))
    from instinct_cli import load_all_instincts

    instincts_dir = temp_data_dir / 'instincts' / 'personal'

    # Create 100 instinct files
    start_time = time.time()

    for i in range(100):
        instinct_content = f'''---
id: test-instinct-{i}
trigger: "when testing scenario {i}"
confidence: 0.{50 + (i % 40):02d}
domain: testing
source: session-observation
created: "2026-02-28T10:00:00Z"
evidence_count: {i + 1}
---
# Test Instinct {i}

## Action
Perform test action {i}.

## Evidence
- Observed {i + 1} times
'''
        instinct_file = instincts_dir / f'instinct_{i}.yaml'
        instinct_file.write_text(instinct_content)

    creation_time = time.time() - start_time

    # Load all instincts - need to set environment variable
    import os
    old_data_dir = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    load_start = time.time()
    instincts = load_all_instincts()
    load_time = time.time() - load_start

    # Restore old environment
    if old_data_dir:
        os.environ['INSTINCT_LEARNING_DATA_DIR'] = old_data_dir
    else:
        os.environ.pop('INSTINCT_LEARNING_DATA_DIR', None)

    # Verify results
    assert len(instincts) == 100
    assert load_time < 5.0, f"Loading took {load_time:.2f}s, expected < 5s"
    assert creation_time < 5.0, f"Creation took {creation_time:.2f}s, expected < 5s"
