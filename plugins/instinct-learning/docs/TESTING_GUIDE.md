# Testing Guide

This guide covers running tests, writing tests, and troubleshooting common issues.

## Table of Contents

- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Coverage](#coverage)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

Run all tests:
```bash
./tests/run-all.sh
```

Run specific test suite:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/scenarios/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=scripts --cov-report=html
open htmlcov/index.html
```

---

## Running Tests

### Run All Tests

```bash
# Using the run-all script
./tests/run-all.sh

# Using pytest directly
pytest tests/ -v
```

### Run by Type

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Scenario tests only
pytest tests/scenarios/ -v
```

### Run by Marker

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only unit tests
pytest -m "unit" -v

# Run only integration tests
pytest -m "integration" -v

# Run only scenario tests
pytest -m "scenario" -v
```

### Run Specific Test File

```bash
# Single test file
pytest tests/unit/test_confidence.py -v

# Multiple test files
pytest tests/unit/test_confidence.py tests/unit/test_parser.py -v
```

### Run Specific Test

```bash
# By function name
pytest tests/unit/test_confidence.py::TestCalculateEffectiveConfidence::test_no_decay_when_recent -v

# By test ID
pytest tests/unit/test_confidence.py::TestCalculateEffectiveConfidence -k "decay" -v
```

---

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures
├── fixtures.py                  # Custom fixtures
├── run-all.sh                   # Run all tests script
│
├── unit/                        # Unit tests
│   ├── __init__.py
│   ├── test_cli_confidence.py   # Confidence calculation tests
│   ├── test_cli_parser.py       # Parser tests
│   ├── test_cli_import.py       # Import parsing tests
│   ├── test_cli_prune.py        # Prune logic tests
│   ├── test_cli_errors.py       # Error handling tests
│   ├── test_confidence_decay.py # Comprehensive decay tests
│   ├── test_instinct_parser.py  # Parser tests
│   ├── test_file_io.py          # File I/O tests
│   ├── test_agent_dispatch.py   # Agent dispatch tests
│   ├── test_hook_script_properties.py  # Hook script tests
│   └── test_observe_sh.py       # Hook behavior tests
│
├── integration/                 # Integration tests
│   ├── __init__.py
│   ├── test_cli_integration.py  # CLI integration tests
│   ├── test_hooks_integration.py # Hooks integration tests
│   ├── test_analyzer_integration.py # Analyzer agent tests
│   └── test_cli_workflows.py    # End-to-end workflow tests
│
└── scenarios/                   # Scenario tests
    ├── __init__.py
    ├── test_edge_cases.py       # Edge case scenarios
    ├── test_error_handling.py   # Error handling scenarios
    ├── test_data_integrity.py   # Data integrity scenarios
    └── test_performance.py      # Performance scenarios
```

---

## Writing Tests

### Test File Template

```python
"""Tests for <module>."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from <module> import <function>


@pytest.mark.unit
class Test<FunctionName>:
    """Tests for <function>."""

    def test_<specific_behavior>(self):
        """Test that <specific_behavior> works correctly."""
        # Arrange
        input_value = "..."

        # Act
        result = <function>(input_value)

        # Assert
        assert result == expected_value
```

### Test Organization

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test module interactions
3. **Scenario Tests**: Test end-to-end workflows

### Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>` or `Test<FunctionName>`
- Test methods: `test_<behavior>_under_<condition>`

### Test Markers

```python
@pytest.mark.unit
def test_something():
    """Unit test."""

@pytest.mark.integration
def test_something_else():
    """Integration test."""

@pytest.mark.scenario
@pytest.mark.slow
def test_scenario():
    """Scenario test (slow)."""
```

---

## Fixtures

### Using Fixtures

```python
def test_with_fixture(temp_data_dir):
    """Test using temporary data directory."""
    # temp_data_dir is automatically cleaned up
    assert temp_data_dir.exists()
```

### Available Fixtures

#### `temp_data_dir`

Creates a temporary data directory for testing.

```python
@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory."""
    data_dir = tmp_path / 'instinct-data'
    personal_dir = data_dir / 'instincts' / 'personal'
    personal_dir.mkdir(parents=True)

    # Create test data
    (personal_dir / 'test.yaml').write_text('...')

    yield data_dir

    # Cleanup (automatic with tmp_path)
```

#### `mock_observations`

Creates mock observation data.

```python
@pytest.fixture
def mock_observations():
    """Create mock observations."""
    return [
        {
            'timestamp': '2026-02-28T10:00:00Z',
            'tool': 'Edit',
            'file': '/path/to/file.py'
        },
        # ... more observations
    ]
```

---

## Coverage

### Check Coverage

```bash
# Terminal report
pytest tests/ --cov=scripts --cov-report=term-missing

# HTML report
pytest tests/ --cov=scripts --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest tests/ --cov=scripts --cov-report=xml
```

### Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| cli_parser.py | 100% | ✅ 100% |
| commands/ | 80% | ✅ 81-90% |
| utils/ | 90% | ✅ 91-100% |
| **Overall** | **50%** | ✅ **68%** |

### Missing Coverage Areas

```bash
# Show missing lines
pytest tests/ --cov=scripts --cov-report=term-missing | grep "Missing"
```

---

## Troubleshooting

### Import Errors

**Problem:** `ImportError: cannot import name 'X' from 'instinct_cli'`

**Solution:** Import from the correct module:
```python
# ❌ Old way
from instinct_cli import parse_instinct_file

# ✅ New way
from utils.instinct_parser import parse_instinct_file
```

### Path Issues

**Problem:** Tests can't find scripts directory

**Solution:** Add scripts directory to path:
```python
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))
```

### Test Isolation

**Problem:** Tests interfere with each other

**Solution:** Use fixtures for isolation:
```python
@pytest.fixture
def isolated_env(tmp_path):
    """Create isolated environment."""
    env_dir = tmp_path / 'test-env'
    env_dir.mkdir()

    # Set up
    original = os.environ.get('INSTINCT_LEARNING_DATA_DIR')
    os.environ['INSTINCT_LEARNING_DATA_DIR'] = str(env_dir)

    yield env_dir

    # Tear down
    if original:
        os.environ['INSTINCT_LEARNING_DATA_DIR'] = original
    else:
        os.environ.pop('INSTINCT_LEARNING_DATA_DIR', None)
```

### Slow Tests

**Problem:** Tests take too long

**Solution:**
1. Skip slow tests during development:
   ```bash
   pytest -m "not slow" -v
   ```

2. Use parallel execution:
   ```bash
   pytest -n auto -v
   ```

3. Mock expensive operations:
   ```python
   @pytest.fixture
   def mock_file_io(monkeypatch):
       """Mock expensive file I/O."""
       def mock_load():
           return [{'id': 'test'}]
       monkeypatch.setattr('utils.file_io.load_all_instincts', mock_load)
   ```

### Debugging Tests

**Run with output:**
```bash
pytest tests/unit/test_confidence.py -v -s
```

**Run with debugger:**
```bash
pytest tests/unit/test_confidence.py -v --pdb
```

**Run on first failure:**
```bash
pytest tests/ -v -x
```

**Show local variables on failure:**
```bash
pytest tests/ -v -l
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pyyaml

      - name: Run tests
        run: |
          pytest tests/ --cov=scripts --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Keep tests focused
3. **Descriptive names**: Use test names that describe what is being tested
4. **Fixtures**: Use fixtures for common setup
5. **Mock external dependencies**: Don't depend on external resources
6. **Test error cases**: Test both success and failure paths
7. **Keep tests fast**: Avoid unnecessary delays
8. **Independent tests**: Tests should not depend on each other

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
