---
name: instinct:import
description: Import instincts from file or URL
---

# Import Instincts

Import instincts from a file or URL to inherit learned behaviors from others.

## Usage

```
/instinct:import <source> [--dry-run] [--force] [--min-confidence <0.0-1.0>]
```

## Arguments

- `<source>` - File path or URL to import from

## Options

- `--dry-run` - Preview without importing
- `--force` - Skip confirmation prompt
- `--min-confidence <n>` - Minimum confidence threshold

## Example

Import from a file:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import team-instincts.md
```

Import from URL:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import https://example.com/instincts.md
```

## What Happens

1. Parses instincts from source
2. Compares with existing instincts
3. Shows new, updated, and duplicate instincts
4. Prompts for confirmation
5. Saves to `~/.claude/instinct-learning/instincts/inherited/`

## Implementation

**IMPORTANT: This command ONLY runs the CLI tool. Do NOT dispatch any agents or perform any analysis.**

Execute this command directly:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import <source> [options]
```

## Related Commands

- `/instinct:export` - Export instincts
- `/instinct:status` - View all instincts
