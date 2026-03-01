# Changelog

All notable changes to the instinct-learning plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **CRITICAL: Race condition in archive cleanup** - Prevents data loss when analyzer takes >5 minutes to process observations
  - Added `.processing` marker check before cleanup
  - Double protection: marker check + `! -name "*.processing"` find pattern
  - Added integration tests (`tests/integration/test_archive_cleanup_race.py`)
- **CRITICAL: YAML injection vulnerability** - Prevents remote code execution via malicious instinct files
  - Replaced manual string parsing with `yaml.safe_load()`
  - Added confidence range validation (0.0-1.0)
  - Added control character sanitization
  - Added frontmatter key whitelisting
  - Added security tests (`tests/unit/test_instinct_parser_security.py`)
- **Test coverage increased to 95%** (from 16%)
  - Added error handling tests for `file_io.py` (`tests/unit/test_file_io_errors.py`)
  - Added edge case tests for confidence calculation (`tests/unit/test_confidence_edge_cases.py`)
  - Added concurrent operation tests (`tests/integration/test_concurrent_operations.py`)
  - Total test suite: 282 tests (all passing)

### Security
- Instinct parser now uses `yaml.safe_load()` to prevent arbitrary code execution
- All instinct frontmatter keys are validated against an ALLOWED_KEYS whitelist
- Confidence values are validated to be within 0.0-1.0 range
- Control characters are sanitized from string values

### Changed
- `scripts/utils/instinct_parser.py` - Complete rewrite using safe YAML parsing
- `hooks/observe.sh` - Added race condition prevention in archive cleanup

### Added
- Standard project files: `.gitignore`, `pyproject.toml`, `LICENSE`
- `strict` and `homepage` fields to plugin manifest
- Comprehensive documentation: `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`

## [2.0.0] - 2025-02-28

### Added
- Evolver agent for semantic clustering of instincts
- Automatic evolution into skills, commands, and agents
- Nested skills directory structure for better organization
- 50-item limit for evolution processing
- Merge strategies for similar instincts
- Prune strategy for low-confidence instincts

### Changed
- Removed evolve functionality from Python CLI (now handled by evolver agent)
- Observer agent replaced by analyzer agent
- Data flow simplified: observation → analysis → evolution

### Removed
- `/instinct:evolve` CLI command (replaced by agent dispatch)
- `evolve` Python command module

### Fixed
- Relative path fragility in analyzer prune command
- Observation threshold warning messages

## [1.0.0] - 2025-02-15

### Added
- Initial release of instinct-learning plugin
- Observation capture via async hooks (PreToolUse, PostToolUse, Stop)
- Analyzer agent for pattern detection
- Confidence scoring (0.3-0.9 range)
- CLI commands: status, analyze, import, export, prune, decay
- Comprehensive test suite (unit, integration, scenario tests)
- Configuration schema and examples
- Documentation: README, CLI API, Configuration Guide, Testing Guide

### Features
- Non-blocking atomic locking for hook scripts
- JSON-based observation storage with numbered archives
- Environment variable support (`INSTINCT_LEARNING_DATA_DIR`)
- Debug mode for troubleshooting
- Weekly confidence decay algorithm
- Domain-based instinct categorization

[Unreleased]: https://github.com/zhengyuli/oh-my-claude-code/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/zhengyuli/oh-my-claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/zhengyuli/oh-my-claude-code/releases/tag/v1.0.0
