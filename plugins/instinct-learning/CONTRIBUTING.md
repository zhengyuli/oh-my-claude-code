# Contributing to Instinct-Learning Plugin

Thank you for your interest in contributing to the instinct-learning plugin! This document provides guidelines and instructions for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Report Bugs](#report-bugs)
- [Suggest Enhancements](#suggest-enhancements)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Claude Code CLI with plugin support

### Installation

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/oh-my-claude-code.git
   cd oh-my-claude-code/plugins/instinct-learning
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

5. Initialize the data directory:
   ```bash
   ./scripts/init-env.sh
   ```

### Project Structure

```
instinct-learning/
├── .claude-plugin/          # Plugin manifest
├── agents/                  # Agent definitions (analyzer, evolver)
├── commands/                # Slash command definitions
├── hooks/                   # Hook scripts
├── scripts/                 # Python CLI implementation
│   ├── commands/            # Command implementations
│   └── utils/               # Utility modules
├── tests/                   # Test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── scenarios/           # Scenario tests
└── docs/                    # Documentation
```

## Running Tests

### Run All Tests

```bash
./tests/run_all.sh
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Scenario tests only
pytest tests/scenarios/ -v

# With coverage
pytest --cov=scripts --cov-report=html
```

### Run Individual Test Files

```bash
pytest tests/unit/test_confidence_decay.py -v
pytest tests/integration/test_analyzer_integration.py -v
```

### Type Checking

```bash
# Run mypy
mypy scripts/

# Run pylint
pylint scripts/
```

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:
- Maximum line length: 100 characters
- Use type hints for all function signatures
- Write docstrings for all public functions and classes

### Code Quality Checklist

Before submitting code, ensure:
- [ ] Code passes all tests (`./tests/run_all.sh`)
- [ ] Code coverage is at 80% or higher
- [ ] No type checking errors (`mypy scripts/`)
- [ ] No pylint warnings (`pylint scripts/`)
- [ ] Code follows the style guide
- [ ] Functions are small (<50 lines)
- [ ] No hardcoded values (use constants or config)
- [ ] Proper error handling with user-friendly messages

### Commit Messages

Follow conventional commits format:
```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

Examples:
```
feat: add confidence decay analysis command
fix: resolve race condition in hook script locking
docs: update architecture documentation
test: add integration tests for analyzer agent
```

### Agent Definition Standards

When creating or modifying agents:

1. **Frontmatter**: Include all required fields
   ```yaml
   ---
   name: agent-name
   description: Clear description of what the agent does
   model: haiku|sonnet|opus
   tools: [list of tools]
   keywords: [discoverable terms]
   ---
   ```

2. **Model Selection**:
   - Use **Haiku** for cost-effective, high-frequency operations
   - Use **Sonnet** for complex reasoning tasks
   - Use **Opus** for deep analysis and research

3. **Structure**:
   - Clear task description
   - Step-by-step process
   - Constraints section
   - Error handling
   - Output format

### Command Definition Standards

When creating slash commands:

1. **Naming**: Use `instinct:<action>` format
2. **Frontmatter**: Include name, description, usage examples
3. **Dispatch**: Either delegate to CLI script or dispatch to agent
4. **Help Text**: Provide clear usage instructions

### Hook Script Standards

Hook scripts must be:
- **Non-blocking**: Use async background execution
- **Atomic**: Use atomic operations for locking
- **Fail-safe**: Graceful degradation on errors
- **Portable**: Work across macOS and Linux

## Submitting Changes

### Pull Request Process

1. Create a new branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request on GitHub:
   - Provide a clear description of the changes
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure all CI checks pass

### Pull Request Checklist

Before submitting a PR:
- [ ] Code follows the coding standards
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventional commits

### Review Process

- Maintainers will review your PR
- Address feedback promptly
- Keep discussion focused and constructive
- Squash commits if requested

## Report Bugs

### Before Reporting

1. Check existing issues
2. Search for similar problems
3. Verify you're using the latest version

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. macOS 14.0, Ubuntu 22.04]
- Python Version: [e.g. 3.11.0]
- Plugin Version: [e.g. 2.0.0]

**Logs**
Error messages or stack traces.

**Additional Context**
Any other relevant information.
```

## Suggest Enhancements

### Enhancement Request Template

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
What other approaches did you consider?

**Additional Context**
Examples, mockups, or references.
```

## Getting Help

- **Documentation**: Start with README.md and docs/
- **Issues**: Search or create GitHub issues
- **Discussions**: Use GitHub Discussions for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to instinct-learning! 🚀
