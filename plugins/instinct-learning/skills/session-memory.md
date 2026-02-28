---
name: session-memory
description: Maintains awareness across sessions, loads context at session start
---

# Session Memory

At the start of each session, provide a brief context summary to maintain continuity across sessions.

## Purpose

- Remember learning progress between sessions
- Surface recent patterns and instincts
- Highlight evolution opportunities
- Provide quick context for continuity

## Trigger

This skill activates:
- At session start (automatically via hook or manual invocation)
- When user asks about learning progress

## Process

1. **Load Session Count**: Read from `~/.claude/instinct-learning/session.json`

2. **Load Recent Instincts**: Get the 3 most recently created/updated instincts

3. **Check Evolution Opportunities**: Find domains with 3+ instincts ready for evolution

4. **Calculate Stats**: Total instincts, domains covered

## Output Format

```
📊 Session #X | Instincts: Y total (Z domains)

Recent learnings:
- [0.7] prefer-functional-style (code-style)
- [0.6] always-test-first (testing)
- [0.5] commit-often (git)

Evolution ready: testing (5 instincts), git (3 instincts)
```

## Implementation

Load and display session context:

```bash
# Get session count
SESSION_COUNT=$(cat ~/.claude/instinct-learning/session.json 2>/dev/null | jq -r '.count // 0')

# Get total instincts
INSTINCT_COUNT=$(find ~/.claude/instinct-learning/instincts -name "*.md" 2>/dev/null | wc -l)

# Get recent instincts
RECENT=$(ls -t ~/.claude/instinct-learning/instincts/personal/*.md 2>/dev/null | head -3)

echo "📊 Session #$SESSION_COUNT | Instincts: $INSTINCT_COUNT total"
echo ""
echo "Recent learnings:"
for file in $RECENT; do
    # Extract id and confidence from frontmatter
    ID=$(grep "^id:" "$file" | cut -d' ' -f2)
    CONF=$(grep "^confidence:" "$file" | cut -d' ' -f2)
    DOMAIN=$(grep "^domain:" "$file" | cut -d' ' -f2)
    echo "- [$CONF] $ID ($DOMAIN)"
done
```

## Configuration

Enable/disable in `~/.claude/instinct-learning/config.json`:

```json
{
  "session": {
    "track_sessions": true,
    "memory_enabled": true
  }
}
```

## Notes

- Session count increments on each Stop hook
- Recent instincts sorted by file modification time
- Evolution opportunities require 3+ instincts with avg confidence ≥ 0.7
