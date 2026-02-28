---
name: instinct:evolve
description: Cluster instincts into skills, commands, or agents
---

# Evolve Instincts

Analyze instincts and cluster related ones into reusable capabilities.

## Usage

```
/instinct:evolve [--generate]
```

## Options

- `--generate` - Actually generate the evolved files (dry-run by default)

## What It Does

1. Groups instincts by trigger patterns
2. Identifies clusters with 3+ related instincts
3. Suggests capability types:
   - **Skills** - High-confidence clusters
   - **Commands** - Workflow instincts
   - **Agents** - Complex multi-step patterns

## Output

```
============================================================
  EVOLVE ANALYSIS - 15 instincts
============================================================

High confidence instincts (>=80%): 5

Potential skill clusters found: 3

## SKILL CANDIDATES

1. Cluster: "when implementing new features"
   Instincts: 4
   Avg confidence: 75%
   Domains: testing, workflow

## COMMAND CANDIDATES (2)

  /new-feature
    From: test-first-approach
    Confidence: 90%
```

## Implementation

**IMPORTANT: This command ONLY runs the CLI tool. Do NOT dispatch any agents or perform any analysis.**

Execute this command directly:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py evolve [--generate]
```

## Related Commands

- `/instinct:status` - View all instincts
- `/instinct:analyze` - Create new instincts (uses observer agent)
