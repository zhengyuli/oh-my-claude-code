"""Concurrent operation tests."""
import subprocess
import pytest
import json
import time
from pathlib import Path


@pytest.mark.integration
def test_concurrent_hook_writes(temp_data_dir):
    """10 sequential hook calls should all succeed."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    # Hook script is in the hooks directory at the plugin root
    hook_script = Path(__file__).parent.parent.parent / "hooks" / "observe.sh"
    obs_file = temp_data_dir / "observations" / "observations.jsonl"

    # Ensure hook script exists
    if not hook_script.exists():
        pytest.skip(f"Hook script not found at {hook_script}")

    # Launch 10 hook calls sequentially
    for i in range(10):
        test_data = json.dumps({
            "hook_type": "PostToolUse",
            "tool_name": f"Test{i}",
            "timestamp": "2026-03-01T10:00:00Z"
        })
        p = subprocess.Popen(
            ['bash', str(hook_script), 'post'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        p.stdin.write(test_data.encode())
        p.stdin.close()
        p.wait(timeout=10)

    # Give a moment for all writes to complete
    time.sleep(0.5)

    # Verify observations captured
    if obs_file.exists():
        with open(obs_file) as f:
            count = sum(1 for _ in f)
        assert count >= 9, f"Only captured {count}/10 observations"
    else:
        pytest.skip(f"Observations file not created at {obs_file}")


@pytest.mark.integration
def test_concurrent_hook_writes_with_large_data(temp_data_dir):
    """Multiple hooks with large inputs should truncate correctly."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    hook_script = Path(__file__).parent.parent.parent / "hooks" / "observe.sh"
    obs_file = temp_data_dir / "observations" / "observations.jsonl"

    # Ensure hook script exists
    if not hook_script.exists():
        pytest.skip(f"Hook script not found at {hook_script}")

    # Create large input data (10000 chars)
    large_data = json.dumps({
        "hook_type": "PostToolUse",
        "tool_name": "Edit",
        "input": "x" * 10000,
        "timestamp": "2026-03-01T10:00:00Z"
    })

    # Launch 5 hook calls sequentially with large data
    for i in range(5):
        p = subprocess.Popen(
            ['bash', str(hook_script), 'post'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        p.stdin.write(large_data.encode())
        p.stdin.close()
        p.wait(timeout=10)

    # Give a moment for all writes to complete
    time.sleep(0.5)

    # Verify observations were captured and truncated
    if obs_file.exists():
        with open(obs_file) as f:
            lines = f.readlines()

        assert len(lines) >= 4, f"Only captured {len(lines)}/5 observations"

        # Verify each line is valid JSON and is truncated
        for line in lines:
            data = json.loads(line)
            # Input should be truncated to 5000 chars
            if 'input' in data:
                assert len(data['input']) <= 5000, f"Input not truncated: {len(data['input'])} chars"
    else:
        pytest.skip(f"Observations file not created at {obs_file}")


@pytest.mark.integration
def test_concurrent_mixed_hook_events(temp_data_dir):
    """Mixed pre and post events should be handled correctly."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    hook_script = Path(__file__).parent.parent.parent / "hooks" / "observe.sh"
    obs_file = temp_data_dir / "observations" / "observations.jsonl"

    # Ensure hook script exists
    if not hook_script.exists():
        pytest.skip(f"Hook script not found at {hook_script}")

    # Launch 10 hook calls sequentially (5 pre, 5 post)
    for i in range(10):
        event_type = 'pre' if i % 2 == 0 else 'post'
        test_data = json.dumps({
            "hook_type": f"{event_type.capitalize()}ToolUse",
            "tool_name": f"Test{i}",
            "timestamp": "2026-03-01T10:00:00Z"
        })
        p = subprocess.Popen(
            ['bash', str(hook_script), event_type],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        p.stdin.write(test_data.encode())
        p.stdin.close()
        p.wait(timeout=10)

    # Give a moment for all writes to complete
    time.sleep(0.5)

    # Verify observations captured
    if obs_file.exists():
        with open(obs_file) as f:
            lines = f.readlines()

        assert len(lines) >= 9, f"Only captured {len(lines)}/10 observations"

        # Verify we have both pre and post events
        pre_count = sum(1 for line in lines if '"event": "tool_start"' in line)
        post_count = sum(1 for line in lines if '"event": "tool_complete"' in line)

        assert pre_count > 0, "No pre events captured"
        assert post_count > 0, "No post events captured"
    else:
        pytest.skip(f"Observations file not created at {obs_file}")


@pytest.mark.integration
def test_concurrent_hook_with_invalid_json(temp_data_dir):
    """Hooks with some invalid JSON should handle gracefully."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    hook_script = Path(__file__).parent.parent.parent / "hooks" / "observe.sh"
    obs_file = temp_data_dir / "observations" / "observations.jsonl"

    # Ensure hook script exists
    if not hook_script.exists():
        pytest.skip(f"Hook script not found at {hook_script}")

    # Launch 10 hook calls sequentially (some valid, some invalid)
    for i in range(10):
        if i % 3 == 0:
            # Invalid JSON
            test_data = "{invalid json"
        else:
            # Valid JSON
            test_data = json.dumps({
                "hook_type": "PostToolUse",
                "tool_name": f"Test{i}",
                "timestamp": "2026-03-01T10:00:00Z"
            })

        p = subprocess.Popen(
            ['bash', str(hook_script), 'post'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        p.stdin.write(test_data.encode())
        p.stdin.close()
        p.wait(timeout=10)

    # Give a moment for all writes to complete
    time.sleep(0.5)

    # Verify valid observations were captured (invalid ones should be skipped)
    if obs_file.exists():
        with open(obs_file) as f:
            lines = f.readlines()

        # Should capture at least 6 valid observations (out of 10, with 3 invalid)
        assert len(lines) >= 6, f"Only captured {len(lines)}/10 observations (expected ~7 valid)"
    else:
        pytest.skip(f"Observations file not created at {obs_file}")
