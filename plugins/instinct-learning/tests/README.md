# Testing Guide for instinct-learning Plugin

## Test Structure

```
tests/
├── unit/           # Unit tests for individual functions
├── integration/    # Integration tests for component interactions
├── scenarios/      # End-to-end scenario tests
├── conftest.py     # Shared pytest fixtures
├── fixtures.py     # Test data fixtures
└── run_all.sh      # Test runner script
```

## Running Tests

### All Tests
```bash
./tests/run_all.sh
# or
pytest tests/ -v
```

### By Category
```bash
./tests/run_all.sh --unit         # Unit tests only
./tests/run_all.sh --integration  # Integration tests only
./tests/run_all.sh --scenario     # Scenario tests only
```

### With Coverage
```bash
./tests/run_all.sh --coverage
# or
pytest --cov=scripts --cov-report=html
```

### Specific Test File
```bash
pytest tests/unit/test_cli_parser.py -v
```

### Specific Test
```bash
pytest tests/unit/test_cli_parser.py::TestParseInstinctFile::test_parse_single_instinct -v
```

## Writing Tests

1. **Unit Tests**: Test individual functions in isolation
   - Use `@pytest.mark.unit`
   - Mock external dependencies
   - Test edge cases

2. **Integration Tests**: Test component interactions
   - Use `@pytest.mark.integration`
   - Use real components (subprocess, files)
   - Test workflows

3. **Scenario Tests**: Test end-to-end scenarios
   - Use `@pytest.mark.scenario`
   - Simulate real usage
   - Test error handling

## Fixtures

Key fixtures in `conftest.py`:
- `temp_data_dir` - Isolated temporary data directory
- `temp_home` - Sets HOME to temp directory
- `sample_observation` - Single observation record
- `sample_instinct_yaml` - Sample instinct in YAML format
- `mock_observations_file` - Pre-populated observations file

## Coverage Goals

- Line Coverage: 80%+
- Branch Coverage: 70%+
- Function Coverage: 90%+

View coverage report: `open htmlcov/index.html`
