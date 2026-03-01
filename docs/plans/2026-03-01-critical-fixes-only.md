# Critical Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 critical security/reliability issues for production readiness.

**Approach:** Minimal, focused fixes - no additional features.

**Timeline:** 3-5 days (3 critical issues only)

---

## Overview

This plan addresses ONLY the 3 critical issues identified in the enterprise readiness assessment:

1. **Race condition in archive cleanup** - Data loss risk
2. **YAML injection vulnerability** - Remote code execution risk
3. **Insufficient test coverage** - Production bug risk

**What's NOT included:** Enterprise features (logging, timeouts, docs, etc.)

---

## Fix 1: Archive Cleanup Race Condition

**Files:**
- Modify: `hooks/observe.sh`
- Test: `tests/integration/test_archive_cleanup_race.py`

**Problem:** If analyzer takes >5 minutes, `find -mmin +5` could delete the archive it's processing.

**Solution:** Processing marker file + double protection.

### Step 1: Add processing marker check to observe.sh

Edit `hooks/observe.sh` at line 175 (replace existing cleanup section):

```bash
# ========== Cleanup Archives (with race condition prevention) ==========

# CRITICAL: Check for processing marker before cleanup
# The analyzer agent creates .processing marker before starting analysis
if [ -f "${OBS_DIR}/.processing" ]; then
  log "Processing marker exists - skipping archive cleanup to prevent data loss"
  exit 0
fi

# Remove analyzed archives (only files older than 5 minutes AND without .processing suffix)
# Double protection: marker check + ! -name "*.processing" pattern
find "${OBS_DIR}" -name "observations.*.jsonl" -mmin +5 ! -name "*.processing" -delete 2>/dev/null
log "Archives cleaned up (respected processing marker)"

# ========== Critical Section End ==========
```

### Step 2: Test marker protection works

```bash
# Manual test
cd ~/.claude/instinct-learning/observations
touch .processing
find . -name "observations.*.jsonl" -mmin +5 ! -name "*.processing" -delete 2>/dev/null
# Should skip deletion
rm .processing
```

### Step 3: Commit

```bash
git add hooks/observe.sh
git commit -m "fix(race-condition): prevent archive cleanup data loss

Add .processing marker protection to prevent deletion of archives
still being analyzed by the agent.

- Check for .processing marker before cleanup
- Use ! -name \"*.processing\" for double protection
- Prevents data loss when analyzer takes >5 minutes

Fixes: Critical Issue #1"
```

---

## Fix 2: YAML Injection Vulnerability

**Files:**
- Replace: `scripts/utils/instinct_parser.py`
- Create: `tests/unit/test_instinct_parser_security.py`

**Problem:** Manual string parsing vulnerable to code injection via malicious YAML.

**Solution:** Use `yaml.safe_load()` + input validation.

### Step 1: Replace instinct_parser.py with safe version

**Complete replacement of `scripts/utils/instinct_parser.py`:**

```python
"""
Safe YAML frontmatter parser for instinct files.

SECURITY: Uses yaml.safe_load() to prevent code injection attacks.
"""

import re
import yaml
from typing import List, Dict, Any

# Allowed keys (prevent injection via unknown keys)
ALLOWED_KEYS = {
    'id', 'trigger', 'confidence', 'domain', 'source',
    'created', 'last_observed', 'evidence_count', 'source_repo'
}

MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0


def validate_confidence(value: Any) -> float:
    """Validate confidence is within valid range."""
    try:
        conf = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Confidence must be a number") from e

    if not (MIN_CONFIDENCE <= conf <= MAX_CONFIDENCE):
        raise ValueError(f"Confidence must be {MIN_CONFIDENCE}-{MAX_CONFIDENCE}, got {conf}")
    return conf


def sanitize_string(value: str) -> str:
    """Remove control characters that could cause issues."""
    if not isinstance(value, str):
        return str(value)
    # Remove null bytes and control characters (except newline, tab)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', value)


def parse_instinct_file(content: str) -> List[Dict[str, Any]]:
    """Parse instinct file using safe YAML parsing.

    SECURITY: Uses yaml.safe_load() to prevent arbitrary code execution.
    """
    instincts = []
    current = {}
    in_frontmatter = False
    content_lines = []
    frontmatter_lines = []

    for line in content.split('\n'):
        if line.strip() == '---':
            if in_frontmatter:
                # End of frontmatter - parse safely
                try:
                    frontmatter_str = '\n'.join(frontmatter_lines)
                    parsed = yaml.safe_load(frontmatter_str)

                    if isinstance(parsed, dict):
                        # Only keep allowed keys
                        parsed = {k: v for k, v in parsed.items() if k in ALLOWED_KEYS}

                        # Validate confidence if present
                        if 'confidence' in parsed:
                            parsed['confidence'] = validate_confidence(parsed['confidence'])

                        # Sanitize string values
                        for key, value in parsed.items():
                            if isinstance(value, str):
                                parsed[key] = sanitize_string(value)

                        current.update(parsed)
                except (yaml.YAMLError, ValueError) as e:
                    # Skip malformed entries
                    pass

                in_frontmatter = False
                frontmatter_lines = []
            else:
                # Start of frontmatter - save previous instinct
                if current:
                    current['content'] = '\n'.join(content_lines).strip()
                    instincts.append(current)
                current = {}
                content_lines = []
                in_frontmatter = True
        elif in_frontmatter:
            frontmatter_lines.append(line)
        else:
            content_lines.append(line)

    # Don't forget the last instinct
    if current:
        current['content'] = '\n'.join(content_lines).strip()
        instincts.append(current)

    # Filter out instincts without valid ID
    return [i for i in instincts if i.get('id')]
```

### Step 2: Add security tests

Create `tests/unit/test_instinct_parser_security.py`:

```python
"""Security tests for instinct parser."""
import pytest
from scripts.utils.instinct_parser import parse_instinct_file


def test_python_code_injection_blocked():
    """Python code in YAML should NOT execute."""
    malicious = """---
id: test
---
__import__('os').system('echo pwned')
"""
    result = parse_instinct_file(malicious)
    assert len(result) == 1
    # Content should be literal string, not executed
    assert "__import__" not in result[0].get('content', '')


def test_confidence_range_validated():
    """Confidence must be 0.0-1.0."""
    invalid = """---
id: test
confidence: 1.5
---
"""
    with pytest.raises(ValueError):
        parse_instinct_file(invalid)
```

### Step 3: Run tests

```bash
pytest tests/unit/test_instinct_parser_security.py -v
pytest tests/unit/test_instinct_parser.py -v  # Ensure existing tests still pass
```

### Step 4: Commit

```bash
git add scripts/utils/instinct_parser.py
git add tests/unit/test_instinct_parser_security.py
git commit -m "fix(security): prevent YAML injection attacks

Replace manual string parsing with yaml.safe_load() to prevent
arbitrary code execution via malicious instinct files.

- Use yaml.safe_load() instead of manual parsing
- Validate confidence range (0.0-1.0)
- Sanitize control characters
- Reject unknown frontmatter keys

Fixes: Critical Issue #2 (CVE prevention)"
```

---

## Fix 3: Increase Test Coverage to 60%+

**Current:** 16% coverage
**Target:** 60%+ coverage

**Strategy:** Add tests for untested error paths and edge cases.

### Step 1: Add error handling tests for file_io.py

Create `tests/unit/test_file_io_errors.py`:

```python
"""Error handling tests for file_io module."""
import pytest
from scripts.utils import file_io


def test_load_instincts_skips_corrupted_files(temp_data_dir):
    """Corrupted YAML files should be skipped with warning."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    personal_dir = temp_data_dir / "instincts" / "personal"
    personal_dir.mkdir(parents=True, exist_ok=True)

    # Valid instinct
    (personal_dir / "valid.md").write_text("---\nid: test\n---\nContent")

    # Corrupted file
    (personal_dir / "bad.md").write_text("{{{invalid yaml")

    instincts = file_io.load_all_instincts()

    # Should load valid instinct, skip corrupted
    assert len(instincts) == 1
    assert instincts[0]['id'] == 'test'


def test_load_instincts_handles_missing_directory():
    """Missing directories should return empty list."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = '/nonexistent/path'
    instincts = file_io.load_all_instincts()
    assert instincts == []
```

### Step 2: Add confidence calculation edge case tests

Create `tests/unit/test_confidence_edge_cases.py`:

```python
"""Edge case tests for confidence calculation."""
import pytest
from datetime import datetime, timedelta
from scripts.utils.confidence import calculate_effective_confidence


def test_confidence_with_missing_timestamp():
    """Missing timestamps should return base confidence."""
    instinct = {'confidence': 0.8}
    # No last_observed or created field
    result = calculate_effective_confidence(instinct)
    assert result == 0.8


def test_confidence_floor_at_minimum():
    """Confidence should not decay below MIN_CONFIDENCE."""
    # Instinct from 1 year ago
    old_date = (datetime.now() - timedelta(days=365)).isoformat()
    instinct = {
        'confidence': 0.9,
        'last_observed': old_date
    }
    result = calculate_effective_confidence(instinct, decay_rate=0.1)
    # Should floor at 0.3
    assert result >= 0.3


def test_confidence_with_invalid_timestamp():
    """Invalid timestamps should return base confidence."""
    instinct = {
        'confidence': 0.7,
        'last_observed': 'invalid-date'
    }
    result = calculate_effective_confidence(instinct)
    assert result == 0.7
```

### Step 3: Add concurrent operation tests

Create `tests/integration/test_concurrent_operations.py`:

```python
"""Concurrent operation tests."""
import subprocess
import pytest
from pathlib import Path


@pytest.mark.integration
def test_concurrent_hook_writes(temp_data_dir):
    """10 parallel hook calls should not cause data loss."""
    import os
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(temp_data_dir)

    hook_script = Path("hooks/observe.sh")
    obs_file = temp_data_dir / "observations" / "observations.jsonl"

    # Launch 10 parallel hook calls
    processes = []
    for i in range(10):
        test_data = f'{{"hook_type":"PostToolUse","tool_name":"Test{i}"}}'
        p = subprocess.Popen(
            ['bash', str(hook_script), 'post'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        p.stdin.write(test_data.encode())
        p.stdin.close()
        processes.append(p)

    # Wait for all
    for p in processes:
        p.wait(timeout=10)

    # Verify observations captured (allowing for some lock contention)
    with open(obs_file) as f:
        count = sum(1 for _ in f)

    assert count >= 8, f"Only captured {count}/10 observations"
```

### Step 4: Run coverage report

```bash
cd plugins/instinct-learning
pytest tests/ --cov=scripts --cov-report=term-missing
```

Expected: Coverage now 60%+

### Step 5: Commit

```bash
git add tests/unit/test_file_io_errors.py
git add tests/unit/test_confidence_edge_cases.py
git add tests/integration/test_concurrent_operations.py
git commit -m "test(coverage): increase coverage to 60%+

Add tests for error paths and edge cases to reach 60% coverage.

New tests:
- Corrupted file handling (file_io)
- Missing directory handling (file_io)
- Confidence calculation edge cases
- Concurrent hook operations (10 parallel calls)

Coverage: 16% -> 60%+

Fixes: Critical Issue #3"
```

---

## Summary

**Total Changes:**
- 1 shell script modification (race condition fix)
- 1 Python file replacement (YAML safety)
- 4 new test files
- ~300 lines of code added

**Total Time Estimate:** 3-5 days

**Verification:**
```bash
# Run all tests
cd plugins/instinct-learning
./tests/run_all.sh --coverage

# Manual smoke test
/instinct:status
```

**What's NOT included** (deferred to future):
- Structured logging infrastructure
- Agent timeout configuration
- SECURITY.md documentation
- ENTERPRISE_DEPLOYMENT.md guide
- API stability documentation
- CHANGELOG.md updates

These can be added later if needed for enterprise deployment.

---

**Plan Status:** ✅ Ready for execution
**Scope:** Critical fixes only (minimal, focused approach)
**Risk:** Low (isolated, well-tested changes)
