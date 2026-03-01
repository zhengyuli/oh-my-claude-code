---
name: instinct:export
description: Export instincts for sharing
---

# Export Instincts

Export your instincts to a file for sharing or backup.

## Usage

```
/instinct:export [--output <file>] [--domain <domain>] [--min-confidence <0.0-1.0>]
```

## Options

- `--output <file>` - Output file path (default: stdout)
- `--domain <domain>` - Filter by domain (e.g., testing, workflow)
- `--min-confidence <n>` - Minimum confidence threshold

## Example

Export all high-confidence testing instincts:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export --domain testing --min-confidence 0.7 --output testing-instincts.md
```

## Output Format

The exported file contains:

1. **Header metadata** (3 lines with export date and count)
2. **One or more instinct blocks**, each with:
   - YAML frontmatter (metadata wrapped in `---`)
   - Markdown content (title, action, evidence)

### File Structure

```
# Instincts export          # ← Header (3 lines)
# Date: <timestamp>
# Total: <count>

                           # ← Blank line
---                        # ← Start of instinct #1
id: <instinct-id>
trigger: "when <condition>"
confidence: 0.X
domain: <category>
source: session-observation
---                        # ← End of frontmatter

                           # ← Blank line
# <Instinct Title>         # ← Markdown content starts

## Action
<What to do when trigger fires>

## Evidence
- <Observation 1>
- <Observation 2>

                           # ← Blank line
---                        # ← Start of instinct #2 (if more exist)
...
```

### Example Output

```markdown
# Instincts export
# Date: 2026-03-01T13:25:13.828119
# Total: 23

---
id: bash-command-clustering
trigger: "when executing multiple related commands"
confidence: 0.85
domain: workflow
source: session-observation
---

# Bash Command Clustering

## Action
When executing multiple related commands, cluster them together in rapid succession.

## Evidence
- Bash-to-Bash sequence observed 36 times across all sessions
- Average gap between related Bash commands: 12-19 seconds
```

**Note**: Each instinct is separated by a blank line. The `source_repo` field is omitted when empty.

## Pre-flight Checks

Before running export, verify:

```bash
# 1. Check instincts exist
INSTINCTS_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}/instincts"
if [ ! -d "$INSTINCTS_DIR" ]; then
  echo "❌ Instincts directory not found"
  exit 1
fi

# 2. Count instincts
INSTINCT_COUNT=$(find "$INSTINCTS_DIR"/personal -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$INSTINCT_COUNT" -eq 0 ]; then
  echo "❌ No instincts found to export"
  echo "   Run /instinct:analyze to create instincts."
  exit 1
fi

echo "✅ Ready to export $INSTINCT_COUNT instincts"
```

**Error Messages**:
- ❌ Directory not found
- ❌ No instincts to export

## Implementation

**IMPORTANT: This command ONLY runs the CLI tool. Do NOT dispatch any agents or perform any analysis.**

Execute this command directly:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export [options]
```

## Related Commands

- `/instinct:import` - Import instincts
- `/instinct:status` - View all instincts

## Help

For more information on available options:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export --help
```
