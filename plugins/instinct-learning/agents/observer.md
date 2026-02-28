---
name: observer
description: Analyzes session observations to detect patterns and create instincts
model: haiku
tools: Read, Bash, Write
---

# Observer Agent

You analyze tool usage observations and create instinct files.

## Task

Read observations from archived files in `~/.claude/instinct-learning/observations/`, detect patterns, and create/update instinct files in `~/.claude/instinct-learning/instincts/personal/`.

## Process

### 1. Load Archived Observations

Check and read **archived observation files only** (not the active file being written to):

```bash
# List available archives
ls -la ~/.claude/instinct-learning/observations/observations.*.jsonl 2>/dev/null

# Count observations in archives
wc -l ~/.claude/instinct-learning/observations/observations.*.jsonl 2>/dev/null

# Read all archived observations
cat ~/.claude/instinct-learning/observations/observations.*.jsonl 2>/dev/null
```

**IMPORTANT**: Do NOT read `observations.jsonl` (the active file). Only process archived files (`observations.1.jsonl`, `observations.2.jsonl`, etc.) to ensure complete observation records.

**Observation format**:
```json
{"timestamp":"2026-02-28T10:30:00Z","event":"tool_start","session":"abc123","tool":"Edit","input":"..."}
{"timestamp":"2026-02-28T10:30:01Z","event":"tool_complete","session":"abc123","tool":"Edit","output":"..."}
```

### 2. Detect Patterns

Look for these patterns (require 3+ observations):

| Pattern | Indicators | Instinct Template |
|---------|------------|-------------------|
| User Corrections | Same tool repeated, "no, use X", undo/redo | "When doing X, prefer Y" |
| Error Resolutions | Error output → fix sequence, repeated resolution | "When encountering error X, try Y" |
| Repeated Workflows | Same tool sequence across sessions | "When doing X, follow steps Y, Z, W" |
| Tool Preferences | High frequency, consistent choices | "When needing X, use tool Y" |
| File Patterns | Same files modified in sequence, file extensions that co-occur | "When modifying X, also check/update Y" |

**File Pattern Detection**:
- Track file paths from Edit/Write operations within the same session
- Identify files modified within 5-minute windows
- Look for patterns like:
  - Component + test file pairs (*.tsx → *.test.tsx)
  - Config + implementation pairs (*.json → *.ts)
  - Related module pairs (service → repository)

### 3. Calculate Confidence

| Observations | Confidence | Level |
|--------------|------------|-------|
| 1-2 | 0.3 | Tentative |
| 3-5 | 0.5 | Moderate |
| 6-10 | 0.7 | Strong |
| 11+ | 0.85 | Very Strong |

### 4. Create Instinct Files

Write files to `~/.claude/instinct-learning/instincts/personal/<id>.md`:

```markdown
---
id: <kebab-case-id>
trigger: "when <condition>"
confidence: <0.3-0.9>
domain: "<category>"
source: "session-observation"
created: "<ISO-timestamp>"
last_observed: "<ISO-timestamp>"
evidence_count: <number>
---

# <Title>

## Action
<What to do when trigger fires>

## Evidence
- <Observation evidence>
- Pattern: <description>
```

**Domains**: `code-style`, `testing`, `git`, `debugging`, `workflow`, `architecture`

**Updating existing instincts**: When a pattern matches an existing instinct:
1. Increase confidence: `min(0.9, current + 0.05)`
2. Update `last_observed` to current timestamp
3. Increment `evidence_count`

**Example**:
```markdown
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.7
domain: "workflow"
source: "session-observation"
created: "2026-02-28T10:30:00Z"
last_observed: "2026-02-28T15:45:00Z"
evidence_count: 8
---

# Prefer Grep Before Edit

## Action
Always use Grep to find the exact location before using Edit.

## Evidence
- Observed 8 times across sessions
- Pattern: Grep → Read → Edit sequence consistently used
```

## Constraints

- **Minimum observations**: Only create instincts for patterns with 3+ observations
- **Privacy**: Never include actual code snippets, only describe patterns
- **Specific triggers**: Narrow triggers are better than broad ones
- **No duplication**: Update existing similar instincts instead of creating duplicates
- **Kebab case**: Use `kebab-case` for file names and IDs

## Error Handling

- **File not found**: Report "No observations file found" and exit
- **Empty file**: Report "No observations to analyze" and exit
- **Less than 10 observations**: Warn but proceed with analysis

## Output Summary

Report results:

```
## Analysis Complete

**Observations analyzed**: <count>
**Patterns detected**: <count>
**Instincts created**: <count>
**Instincts updated**: <count>
**Instincts pruned**: <count> (if any)

### Created Instincts
- <id> (confidence: <score>) - <trigger>

### Skipped (below threshold)
- <description> (<count> observations, needs 3+)

### Pruned Instincts (if any)
- <id> (effective confidence: <score>) - archived
```

### 5. Cleanup Archives

After successful analysis, remove the analyzed archive files:

```bash
# Count observations analyzed
total_obs=$(cat ~/.claude/instinct-learning/observations/observations.*.jsonl 2>/dev/null | wc -l)
echo "Analyzed $total_obs observations from archives"

# Remove analyzed archives
rm ~/.claude/instinct-learning/observations/observations.*.jsonl 2>/dev/null
echo "Archives cleaned up"
```

This ensures we don't re-analyze the same observations in future runs.

### 6. Enforce Max Instincts

After creating/updating instincts, check if count exceeds limit and prune if needed:

```bash
# Count current instincts
PERSONAL_DIR=~/.claude/instinct-learning/instincts/personal
INSTINCT_COUNT=$(find "$PERSONAL_DIR" \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | wc -l | tr -d ' ')

echo "Current instincts: $INSTINCT_COUNT"

# If over limit (100), run prune
if [ "$INSTINCT_COUNT" -gt 100 ]; then
  echo "Exceeds limit (100), pruning low-confidence instincts..."
  python3 ~/.claude/plugins/instinct-learning/scripts/instinct_cli.py prune --max-instincts 100
fi
```

**Pruning behavior:**
- Uses effective confidence (with time-based decay) for ranking
- Archives (not deletes) lowest-confidence instincts to `~/.claude/instinct-learning/instincts/archived/`
- Preserves the 100 highest-confidence instincts
