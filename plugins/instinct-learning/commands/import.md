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
5. Saves each instinct to a separate file in `~/.claude/instinct-learning/instincts/inherited/`
   - Filename: `{instinct-id}.md`
   - Example: `bash-command-clustering.md`

## Pre-flight Checks

Before running import, verify:

```bash
SOURCE="$1"  # First argument

# 1. Check source provided
if [ -z "$SOURCE" ]; then
  echo "❌ No source specified"
  echo "   Usage: /instinct:import <file.md or URL>"
  exit 1
fi

# 2. Check file/URL accessibility
if [[ "$SOURCE" == http://* ]] || [[ "$SOURCE" == https://* ]]; then
  # URL source - check accessibility
  if ! curl -fIs "$SOURCE" >/dev/null 2>&1; then
    echo "❌ URL not accessible: $SOURCE"
    exit 1
  fi
else
  # File source - check existence
  if [ ! -f "$SOURCE" ]; then
    echo "❌ File not found: $SOURCE"
    exit 1
  fi

  # Check format
  if ! grep -q -E '^---$' "$SOURCE"; then
    echo "⚠️  File may not be in instinct format (missing frontmatter)"
    echo "   Continue anyway? (y/N)"
    read -r response
    if [ "$response" != "y" ]; then
      exit 0
    fi
  fi
fi

echo "✅ Pre-flight checks passed"
```

**Error Messages**:
- ❌ No source specified
- ❌ File not found
- ❌ URL not accessible
- ⚠️  Invalid format (with continue option)

## Implementation

**IMPORTANT: This command ONLY runs the CLI tool. Do NOT dispatch any agents or perform any analysis.**

Execute this command directly:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import <source> [options]
```

## Related Commands

- `/instinct:export` - Export instincts
- `/instinct:status` - View all instincts

## Help

For more information on available options:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import --help
```
