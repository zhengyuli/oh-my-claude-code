# Changelog

All notable changes to the instinct-learning plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
