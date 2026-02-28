"""
Test fixtures for instinct-learning plugin tests.

This module provides sample data for testing.
"""

import json
from pathlib import Path

# Sample instinct YAML content for testing
SAMPLE_INSTINCT_YAML = '''---
id: sample-instinct
trigger: "when writing Python code"
confidence: 0.85
domain: code-style
source: session-observation
created: "2026-02-28T10:00:00Z"
evidence_count: 5
---
# Sample Instinct

## Action
Always use type hints in function definitions.

## Evidence
- Observed 5 times in session test-123
- Pattern: def func(param: type) -> type
'''

# Multiple instincts in one file
MULTIPLE_INSTINCTS_YAML = '''---
id: first-instinct
trigger: "when starting a new file"
confidence: 0.75
domain: workflow
---
Start with imports and docstring.

---
id: second-instinct
trigger: "when fixing bugs"
confidence: 0.80
domain: debugging
---
Write a test that reproduces the bug first.

---
id: third-instinct
trigger: "when committing changes"
confidence: 0.90
domain: git
---
Always run tests before committing.
'''

# Invalid instinct (missing id)
INVALID_INSTINCT_YAML = '''---
trigger: "invalid"
confidence: 0.5
---
This has no ID.
'''

# Sample observations for testing
SAMPLE_OBSERVATIONS = [
    {
        "timestamp": "2026-02-28T10:00:00Z",
        "event": "tool_start",
        "tool": "Grep",
        "input": json.dumps({"pattern": "def test_", "path": "/project"}),
        "session": "test-session-1"
    },
    {
        "timestamp": "2026-02-28T10:00:05Z",
        "event": "tool_complete",
        "tool": "Grep",
        "output": "Found 5 matches",
        "session": "test-session-1"
    },
    {
        "timestamp": "2026-02-28T10:00:10Z",
        "event": "tool_start",
        "tool": "Read",
        "input": json.dumps({"file_path": "/project/test_file.py"}),
        "session": "test-session-1"
    },
    {
        "timestamp": "2026-02-28T10:00:15Z",
        "event": "tool_complete",
        "tool": "Read",
        "output": "File content...",
        "session": "test-session-1"
    },
    {
        "timestamp": "2026-02-28T10:00:20Z",
        "event": "tool_start",
        "tool": "Edit",
        "input": json.dumps({"file_path": "/project/test_file.py", "old_string": "old", "new_string": "new"}),
        "session": "test-session-1"
    }
]

# Sample hook input for PreToolUse
SAMPLE_PRE_TOOL_USE_INPUT = {
    "hook_type": "PreToolUse",
    "tool_name": "Edit",
    "tool_input": {
        "file_path": "/test/file.py",
        "old_string": "old_code",
        "new_string": "new_code"
    },
    "session_id": "test-session-123"
}

# Sample hook input for PostToolUse
SAMPLE_POST_TOOL_USE_INPUT = {
    "hook_type": "PostToolUse",
    "tool_name": "Edit",
    "tool_input": {
        "file_path": "/test/file.py",
        "old_string": "old_code",
        "new_string": "new_code"
    },
    "tool_output": "Successfully edited file",
    "session_id": "test-session-123"
}

# Sample configuration
SAMPLE_CONFIG = {
    "observation": {
        "enabled": True,
        "max_file_size_mb": 10,
        "archive_after_days": 7,
        "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
        "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate"]
    },
    "instincts": {
        "min_confidence": 0.3,
        "auto_approve_threshold": 0.7,
        "confidence_decay_rate": 0.02,
        "max_instincts": 100
    }
}


def create_test_instinct_file(directory: Path, filename: str = "test_instinct.yaml") -> Path:
    """Create a test instinct file in the specified directory."""
    file_path = directory / filename
    file_path.write_text(SAMPLE_INSTINCT_YAML)
    return file_path


def create_test_observations_file(file_path: Path, count: int = 5) -> Path:
    """Create a test observations file with sample data."""
    observations = []
    for i in range(count):
        obs = {
            "timestamp": f"2026-02-28T10:00:{i:02d}Z",
            "event": "tool_complete",
            "tool": ["Edit", "Read", "Bash", "Grep", "Write"][i % 5],
            "session": f"test-session-{i // 3}"
        }
        observations.append(json.dumps(obs))

    file_path.write_text('\n'.join(observations) + '\n')
    return file_path
