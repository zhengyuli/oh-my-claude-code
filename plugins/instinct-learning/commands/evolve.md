---
name: instinct:evolve
description: Cluster instincts into commands, skills, or agents
keywords: ["evolve", "clustering", "skills", "agents", "commands"]
---

# Evolve Instincts

Analyze instincts and cluster related ones into reusable capabilities.

## Usage

```
/instinct:evolve
```

## What It Does

1. Groups instincts by semantic patterns
2. Identifies clusters with related instincts
3. Generates capability types:
   - **Commands** - Single-action workflows (confidence >= 0.7)
   - **Skills** - 2-5 related instincts (avg confidence >= 0.6)
   - **Agents** - 3+ instincts spanning domains (avg confidence >= 0.7)
4. Enforces 50-item limit per category with intelligent merge/prune

## Prerequisites

- At least 3 instincts across `personal/` and `inherited/` directories
- Instincts with confidence >= 0.6 for meaningful clustering

## Pre-flight Checks

Before dispatching the evolver agent, verify:

```bash
# Set directories
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"
PERSONAL_DIR="${DATA_DIR}/instincts/personal"
INHERITED_DIR="${DATA_DIR}/instincts/inherited"

# 1. Check instincts directories exist
if [ ! -d "$PERSONAL_DIR" ] && [ ! -d "$INHERITED_DIR" ]; then
  echo "❌ Instincts directories not found"
  echo "   Run /instinct:analyze to create instincts, or /instinct:import to import instincts."
  exit 1
fi

# 2. Count instincts across both directories
PERSONAL_COUNT=$(find "$PERSONAL_DIR" -name "*.md" -o -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
INHERITED_COUNT=$(find "$INHERITED_DIR" -name "*.md" -o -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
INSTINCT_COUNT=$((PERSONAL_COUNT + INHERITED_COUNT))

if [ "$INSTINCT_COUNT" -lt 3 ]; then
  echo "❌ Only $INSTINCT_COUNT instincts found (minimum: 3)"
  echo "   Personal: $PERSONAL_COUNT, Inherited: $INHERITED_COUNT"
  echo "   Run /instinct:analyze to create more instincts, or /instinct:import to import instincts."
  exit 1
fi

# 3. Check confidence levels across both directories
HIGH_CONFIDENCE=0
for dir in "$PERSONAL_DIR" "$INHERITED_DIR"; do
  if [ -d "$dir" ]; then
    count=$(find "$dir" \( -name "*.md" -o -name "*.yaml" \) -exec grep -l '^confidence: 0\.[6-9]' {} \; 2>/dev/null | wc -l | tr -d ' ')
    HIGH_CONFIDENCE=$((HIGH_CONFIDENCE + count))
  done
done

if [ "$HIGH_CONFIDENCE" -lt 1 ]; then
  echo "⚠️  No high-confidence instincts (≥0.6) found."
  echo "   Evolution results may be limited. Continue anyway? (y/N)"
  read -r response
  if [ "$response" != "y" ]; then
    exit 0
  fi
fi

echo "✅ Pre-flight checks passed: $INSTINCT_COUNT instincts ready ($HIGH_CONFIDENCE high-confidence)"
echo "   Personal: $PERSONAL_COUNT, Inherited: $INHERITED_COUNT"
```

**Error Messages**:
- ❌ Directories not found
- ❌ Insufficient instincts (< 3)
- ⚠️  Low confidence (with continue option)

## Implementation

**IMPORTANT: This command ONLY dispatches the evolver agent. Do NOT perform evolution yourself.**

Use the Task tool to dispatch the evolver agent:

```
Task tool configuration:
- subagent_type: "instinct-learning:evolver"
- description: "Evolve instincts into commands, skills, and agents"
```

The evolver agent will:
1. Read all instincts from `personal/` and `inherited/` directories
2. Check existing evolved artifacts (commands, skills, agents) to avoid duplicates
3. Perform semantic clustering by domain
4. Generate new artifacts or update existing ones
5. Enforce 50-item limit per category with merge/prune strategies
6. Write to `~/.claude/instinct-learning/evolved/{commands,skills,agents}/`

## Example

```
User: /instinct:evolve

Claude: Dispatching the evolver agent to evolve your instincts...

[Uses Task tool with subagent_type: "instinct-learning:evolver"]

Evolver Agent: Analyzing 8 instincts...

Domains found: workflow (5), testing (2), debugging (1)

Generated artifacts:
- Commands: 3 → evolved/commands/*.md
- Skills: 2 → evolved/skills/*/[SKILL.md] (nested)
- Agents: 1 → evolved/agents/*.md

  Details:
  - glob-read-discovery, test-first, bash-heavy
  - exploration-workflow/SKILL.md, testing-routine/SKILL.md
  - development-flow
```

## Related Commands

- `/instinct:status` - View all learned instincts
- `/instinct:analyze` - Create new instincts (uses analyzer agent)
