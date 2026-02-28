# Instinct-Learning Plugin Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor instinct-learning plugin from v2 code, converting from skill to plugin with manual analysis triggering.

**Architecture:** Hook-based observation capture + manual `/instinct:analyze` command triggers observer agent. No background daemon. Data stored in `~/.claude/instinct-learning/`.

**Tech Stack:** Python 3, Bash, JSON Schema, Markdown

---

## Task 1: Clean Up Old Files

**Files:**
- Delete: All files in `plugins/instinct-learning/` except `.claude-plugin/plugin.json`

**Step 1: Remove old directories and files**

```bash
cd /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning
rm -rf agents commands docs hooks lib scripts skills tests config.schema.json README.md
```

**Step 2: Verify cleanup**

Run: `ls -la /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/`
Expected: Only `.claude-plugin/` directory remains

**Step 3: Commit**

```bash
git add -A plugins/instinct-learning/
git commit -m "chore: clean up old instinct-learning files for refactor"
```

---

## Task 2: Create New Directory Structure

**Files:**
- Create: `plugins/instinct-learning/commands/`
- Create: `plugins/instinct-learning/agents/`
- Create: `plugins/instinct-learning/hooks/`
- Create: `plugins/instinct-learning/scripts/`

**Step 1: Create directories**

```bash
mkdir -p /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/{commands,agents,hooks,scripts}
```

**Step 2: Verify structure**

Run: `ls -la /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/`
Expected: `.claude-plugin/`, `commands/`, `agents/`, `hooks/`, `scripts/` directories

---

## Task 3: Create Configuration Schema

**Files:**
- Create: `plugins/instinct-learning/config.schema.json`

**Step 1: Write config.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Instinct Learning Configuration",
  "description": "Configuration schema for the instinct-learning plugin",
  "type": "object",
  "properties": {
    "observation": {
      "type": "object",
      "description": "Observation capture settings",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true,
          "description": "Enable observation capture via hooks"
        },
        "max_file_size_mb": {
          "type": "integer",
          "default": 10,
          "description": "Maximum observations file size before archiving"
        },
        "archive_after_days": {
          "type": "integer",
          "default": 7,
          "description": "Days before observations are archived"
        },
        "capture_tools": {
          "type": "array",
          "items": { "type": "string" },
          "default": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
          "description": "Tools to capture observations for"
        },
        "ignore_tools": {
          "type": "array",
          "items": { "type": "string" },
          "default": ["TodoWrite", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet"],
          "description": "Tools to ignore in observation capture"
        }
      }
    },
    "instincts": {
      "type": "object",
      "description": "Instinct management settings",
      "properties": {
        "min_confidence": {
          "type": "number",
          "default": 0.3,
          "minimum": 0,
          "maximum": 1,
          "description": "Minimum confidence threshold for instincts"
        },
        "auto_approve_threshold": {
          "type": "number",
          "default": 0.7,
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence level for auto-approval"
        },
        "confidence_decay_rate": {
          "type": "number",
          "default": 0.02,
          "minimum": 0,
          "maximum": 0.1,
          "description": "Weekly confidence decay rate"
        },
        "max_instincts": {
          "type": "integer",
          "default": 100,
          "description": "Maximum number of instincts to retain"
        }
      }
    },
    "evolution": {
      "type": "object",
      "description": "Evolution settings",
      "properties": {
        "cluster_threshold": {
          "type": "integer",
          "default": 3,
          "description": "Minimum instincts required for clustering"
        },
        "auto_evolve": {
          "type": "boolean",
          "default": false,
          "description": "Enable automatic evolution"
        }
      }
    }
  }
}
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/config.schema.json
git commit -m "feat: add config.schema.json for instinct-learning plugin"
```

---

## Task 4: Create Hook Configuration

**Files:**
- Create: `plugins/instinct-learning/hooks/hooks.json`

**Step 1: Write hooks.json**

```json
{
  "description": "Instinct-learning hooks for observation capture",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/observe.sh pre",
            "async": true
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/observe.sh post",
            "async": true
          }
        ]
      }
    ]
  }
}
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/hooks/hooks.json
git commit -m "feat: add hooks.json for instinct-learning plugin"
```

---

## Task 5: Create Observation Hook Script

**Files:**
- Create: `plugins/instinct-learning/hooks/observe.sh`

**Step 1: Write observe.sh**

```bash
#!/bin/bash
# Instinct-Learning - Observation Hook
#
# Captures tool use events for pattern analysis.
# Claude Code passes hook data via stdin as JSON.
#
# This hook runs asynchronously and does not block tool execution.

set -e

DATA_DIR="${HOME}/.claude/instinct-learning"
OBSERVATIONS_FILE="${DATA_DIR}/observations.jsonl"
MAX_FILE_SIZE_MB=10

# Ensure directory exists
mkdir -p "$DATA_DIR"

# Skip if disabled
if [ -f "$DATA_DIR/disabled" ]; then
  exit 0
fi

# Read JSON from stdin (Claude Code hook format)
INPUT_JSON=$(cat)

# Exit if no input
if [ -z "$INPUT_JSON" ]; then
  exit 0
fi

# Parse using python via stdin pipe (safe for all JSON payloads)
PARSED=$(echo "$INPUT_JSON" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)

    # Extract fields - Claude Code hook format
    hook_type = data.get("hook_type", "unknown")
    tool_name = data.get("tool_name", data.get("tool", "unknown"))
    tool_input = data.get("tool_input", data.get("input", {}))
    tool_output = data.get("tool_output", data.get("output", ""))
    session_id = data.get("session_id", "unknown")

    # Truncate large inputs/outputs to 1000 chars
    if isinstance(tool_input, dict):
        tool_input_str = json.dumps(tool_input)[:1000]
    else:
        tool_input_str = str(tool_input)[:1000]

    if isinstance(tool_output, dict):
        tool_output_str = json.dumps(tool_output)[:1000]
    else:
        tool_output_str = str(tool_output)[:1000]

    # Determine event type
    event = "tool_start" if "Pre" in hook_type else "tool_complete"

    print(json.dumps({
        "parsed": True,
        "event": event,
        "tool": tool_name,
        "input": tool_input_str if event == "tool_start" else None,
        "output": tool_output_str if event == "tool_complete" else None,
        "session": session_id
    }))
except Exception as e:
    print(json.dumps({"parsed": False, "error": str(e)}))
')

# Check if parsing succeeded
PARSED_OK=$(echo "$PARSED" | python3 -c "import json,sys; print(json.load(sys.stdin).get('parsed', False))")

if [ "$PARSED_OK" != "True" ]; then
  exit 0
fi

# Archive if file too large
if [ -f "$OBSERVATIONS_FILE" ]; then
  file_size_mb=$(du -m "$OBSERVATIONS_FILE" 2>/dev/null | cut -f1)
  if [ "${file_size_mb:-0}" -ge "$MAX_FILE_SIZE_MB" ]; then
    archive_dir="${DATA_DIR}/observations.archive"
    mkdir -p "$archive_dir"
    mv "$OBSERVATIONS_FILE" "$archive_dir/observations-$(date +%Y%m%d-%H%M%S).jsonl"
  fi
fi

# Build and write observation
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

export TIMESTAMP="$timestamp"
echo "$PARSED" | python3 -c "
import json, sys, os

parsed = json.load(sys.stdin)
observation = {
    'timestamp': os.environ['TIMESTAMP'],
    'event': parsed['event'],
    'tool': parsed['tool'],
    'session': parsed['session']
}

if parsed['input']:
    observation['input'] = parsed['input']
if parsed['output']:
    observation['output'] = parsed['output']

print(json.dumps(observation))
" >> "$OBSERVATIONS_FILE"

exit 0
```

**Step 2: Make executable**

```bash
chmod +x /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/hooks/observe.sh
```

**Step 3: Commit**

```bash
git add plugins/instinct-learning/hooks/observe.sh
git commit -m "feat: add observe.sh hook script for instinct-learning"
```

---

## Task 6: Create Observer Agent

**Files:**
- Create: `plugins/instinct-learning/agents/observer.md`

**Step 1: Write observer.md**

```markdown
---
name: observer
description: Analyzes session observations to detect patterns and create instincts. Uses Haiku for cost-efficiency.
model: haiku
---

# Observer Agent

Analyzes observations from Claude Code sessions to detect patterns and create instincts.

## Input

Reads observations from `~/.claude/instinct-learning/observations.jsonl`:

```jsonl
{"timestamp":"2026-02-28T10:30:00Z","event":"tool_start","session":"abc123","tool":"Edit","input":"..."}
{"timestamp":"2026-02-28T10:30:01Z","event":"tool_complete","session":"abc123","tool":"Edit","output":"..."}
```

## Pattern Detection

Look for these patterns in observations:

### 1. User Corrections
When a user's follow-up message corrects Claude's previous action:
- "No, use X instead of Y"
- "Actually, I meant..."
- Immediate undo/redo patterns

→ Create instinct: "When doing X, prefer Y"

### 2. Error Resolutions
When an error is followed by a fix:
- Tool output contains error
- Next few tool calls fix it
- Same error type resolved similarly multiple times

→ Create instinct: "When encountering error X, try Y"

### 3. Repeated Workflows
When the same sequence of tools is used multiple times:
- Same tool sequence with similar inputs
- File patterns that change together
- Time-clustered operations

→ Create workflow instinct: "When doing X, follow steps Y, Z, W"

### 4. Tool Preferences
When certain tools are consistently preferred:
- Always uses Grep before Edit
- Prefers Read over Bash cat
- Uses specific Bash commands for certain tasks

→ Create instinct: "When needing X, use tool Y"

## Output

Creates/updates instincts in `~/.claude/instinct-learning/instincts/personal/`:

```markdown
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.65
domain: "workflow"
source: "session-observation"
created: "2026-02-28T10:30:00Z"
evidence_count: 8
---

# Prefer Grep Before Edit

## Action
Always use Grep to find the exact location before using Edit.

## Evidence
- Observed 8 times in session abc123
- Pattern: Grep → Read → Edit sequence
- Last observed: 2026-02-28
```

## Confidence Calculation

Initial confidence based on observation frequency:
- 1-2 observations: 0.3 (tentative)
- 3-5 observations: 0.5 (moderate)
- 6-10 observations: 0.7 (strong)
- 11+ observations: 0.85 (very strong)

## Important Guidelines

1. **Be Conservative**: Only create instincts for clear patterns (3+ observations)
2. **Be Specific**: Narrow triggers are better than broad ones
3. **Track Evidence**: Always include what observations led to the instinct
4. **Respect Privacy**: Never include actual code snippets, only patterns
5. **Merge Similar**: If a new instinct is similar to existing, update rather than duplicate
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/agents/observer.md
git commit -m "feat: add observer agent for instinct-learning"
```

---

## Task 7: Create /instinct:analyze Command

**Files:**
- Create: `plugins/instinct-learning/commands/analyze.md`

**Step 1: Write analyze.md**

```markdown
---
name: analyze
description: Analyze observations to detect patterns and create instincts
---

# Analyze Observations

Manually trigger pattern analysis on captured observations to create or update instincts.

## Usage

```
/instinct:analyze
```

## What It Does

1. Reads observations from `~/.claude/instinct-learning/observations.jsonl`
2. Uses the observer agent (Haiku) to detect patterns
3. Creates or updates instincts in `~/.claude/instinct-learning/instincts/personal/`

## Pattern Types Detected

- **User Corrections**: When you correct Claude's previous action
- **Error Resolutions**: When an error is followed by a fix
- **Repeated Workflows**: Same sequence of tools used multiple times
- **Tool Preferences**: Consistent preference for certain tools

## Prerequisites

- At least 10 observations captured
- Observations file exists at `~/.claude/instinct-learning/observations.jsonl`

## Example

After several coding sessions, run:

```
/instinct:analyze
```

The agent will analyze your observations and create instincts.

## Related Commands

- `/instinct:status` - View all learned instincts
- `/instinct:evolve` - Cluster instincts into capabilities
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/commands/analyze.md
git commit -m "feat: add /instinct:analyze command"
```

---

## Task 8: Create /instinct:status Command

**Files:**
- Create: `plugins/instinct-learning/commands/status.md`

**Step 1: Write status.md**

```markdown
---
name: status
description: Show all learned instincts with confidence scores
---

# Instinct Status

Display all learned instincts grouped by domain with confidence scores.

## Usage

```
/instinct:status
```

## What It Shows

- Total number of instincts
- Breakdown by source (personal vs inherited)
- Instincts grouped by domain
- Confidence scores with visual bars

## Output Format

```
============================================================
  INSTINCT STATUS - 12 total
============================================================

  Personal:  8
  Inherited: 4

## WORKFLOW (5)

  ███████░░░  70%  prefer-grep-before-edit
            trigger: when searching for code to modify

## TESTING (3)

  █████████░  90%  test-first-approach
            trigger: when implementing new features

─────────────────────────────────────────────────────────
  Observations: 156 events logged
```

## Implementation

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py status
```

## Related Commands

- `/instinct:analyze` - Trigger pattern analysis
- `/instinct:export` - Export instincts for sharing
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/commands/status.md
git commit -m "feat: add /instinct:status command"
```

---

## Task 9: Create /instinct:evolve Command

**Files:**
- Create: `plugins/instinct-learning/commands/evolve.md`

**Step 1: Write evolve.md**

```markdown
---
name: evolve
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

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py evolve [--generate]
```

## Related Commands

- `/instinct:status` - View all instincts
- `/instinct:analyze` - Create new instincts
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/commands/evolve.md
git commit -m "feat: add /instinct:evolve command"
```

---

## Task 10: Create /instinct:export Command

**Files:**
- Create: `plugins/instinct-learning/commands/export.md`

**Step 1: Write export.md**

```markdown
---
name: export
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

```markdown
# Instincts export
# Date: 2026-02-28T10:30:00Z
# Total: 5

---
id: test-first-approach
trigger: "when implementing new features"
confidence: 0.9
domain: testing
source: session-observation
---

# Test First Approach

## Action
Always write tests before implementation.
```

## Implementation

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py export [options]
```

## Related Commands

- `/instinct:import` - Import instincts
- `/instinct:status` - View all instincts
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/commands/export.md
git commit -m "feat: add /instinct:export command"
```

---

## Task 11: Create /instinct:import Command

**Files:**
- Create: `plugins/instinct-learning/commands/import.md`

**Step 1: Write import.md**

```markdown
---
name: import
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

This command calls the CLI tool:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instinct_cli.py import <source> [options]
```

## Related Commands

- `/instinct:export` - Export instincts
- `/instinct:status` - View all instincts
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/commands/import.md
git commit -m "feat: add /instinct:import command"
```

---

## Task 12: Create CLI Tool

**Files:**
- Create: `plugins/instinct-learning/scripts/instinct_cli.py`

**Step 1: Write instinct_cli.py (based on v2 with updates)**

```python
#!/usr/bin/env python3
"""
Instinct CLI - Manage instincts for Instinct-Learning Plugin

Commands:
  status   - Show all instincts and their status
  import   - Import instincts from file or URL
  export   - Export instincts to file
  evolve   - Cluster instincts into skills/commands/agents
"""

import argparse
import json
import os
import sys
import re
import urllib.request
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

DATA_DIR = Path.home() / ".claude" / "instinct-learning"
INSTINCTS_DIR = DATA_DIR / "instincts"
PERSONAL_DIR = INSTINCTS_DIR / "personal"
INHERITED_DIR = INSTINCTS_DIR / "inherited"
EVOLVED_DIR = DATA_DIR / "evolved"
OBSERVATIONS_FILE = DATA_DIR / "observations.jsonl"

# Ensure directories exist
for d in [PERSONAL_DIR, INHERITED_DIR, EVOLVED_DIR / "skills", EVOLVED_DIR / "commands", EVOLVED_DIR / "agents"]:
    d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# Instinct Parser
# ─────────────────────────────────────────────

def parse_instinct_file(content: str) -> list[dict]:
    """Parse YAML-like instinct file format."""
    instincts = []
    current = {}
    in_frontmatter = False
    content_lines = []

    for line in content.split('\n'):
        if line.strip() == '---':
            if in_frontmatter:
                in_frontmatter = False
            else:
                in_frontmatter = True
                if current:
                    current['content'] = '\n'.join(content_lines).strip()
                    instincts.append(current)
                current = {}
                content_lines = []
        elif in_frontmatter:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == 'confidence':
                    current[key] = float(value)
                else:
                    current[key] = value
        else:
            content_lines.append(line)

    if current:
        current['content'] = '\n'.join(content_lines).strip()
        instincts.append(current)

    return [i for i in instincts if i.get('id')]


def load_all_instincts() -> list[dict]:
    """Load all instincts from personal and inherited directories."""
    instincts = []

    for directory in [PERSONAL_DIR, INHERITED_DIR]:
        if not directory.exists():
            continue
        yaml_files = sorted(
            set(directory.glob("*.yaml"))
            | set(directory.glob("*.yml"))
            | set(directory.glob("*.md"))
        )
        for file in yaml_files:
            try:
                content = file.read_text()
                parsed = parse_instinct_file(content)
                for inst in parsed:
                    inst['_source_file'] = str(file)
                    inst['_source_type'] = directory.name
                instincts.extend(parsed)
            except Exception as e:
                print(f"Warning: Failed to parse {file}: {e}", file=sys.stderr)

    return instincts


# ─────────────────────────────────────────────
# Status Command
# ─────────────────────────────────────────────

def cmd_status(args):
    """Show status of all instincts."""
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts found.")
        print(f"\nInstinct directories:")
        print(f"  Personal:  {PERSONAL_DIR}")
        print(f"  Inherited: {INHERITED_DIR}")
        return

    by_domain = defaultdict(list)
    for inst in instincts:
        domain = inst.get('domain', 'general')
        by_domain[domain].append(inst)

    print(f"\n{'='*60}")
    print(f"  INSTINCT STATUS - {len(instincts)} total")
    print(f"{'='*60}\n")

    personal = [i for i in instincts if i.get('_source_type') == 'personal']
    inherited = [i for i in instincts if i.get('_source_type') == 'inherited']
    print(f"  Personal:  {len(personal)}")
    print(f"  Inherited: {len(inherited)}")
    print()

    for domain in sorted(by_domain.keys()):
        domain_instincts = by_domain[domain]
        print(f"## {domain.upper()} ({len(domain_instincts)})")
        print()

        for inst in sorted(domain_instincts, key=lambda x: -x.get('confidence', 0.5)):
            conf = inst.get('confidence', 0.5)
            conf_bar = '█' * int(conf * 10) + '░' * (10 - int(conf * 10))
            trigger = inst.get('trigger', 'unknown trigger')

            print(f"  {conf_bar} {int(conf*100):3d}%  {inst.get('id', 'unnamed')}")
            print(f"            trigger: {trigger}")

            content = inst.get('content', '')
            action_match = re.search(r'## Action\s*\n\s*(.+?)(?:\n\n|\n##|$)', content, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip().split('\n')[0]
                print(f"            action: {action[:60]}{'...' if len(action) > 60 else ''}")

            print()

    if OBSERVATIONS_FILE.exists():
        obs_count = sum(1 for _ in open(OBSERVATIONS_FILE))
        print(f"─────────────────────────────────────────────────────────")
        print(f"  Observations: {obs_count} events logged")
        print(f"  File: {OBSERVATIONS_FILE}")

    print(f"\n{'='*60}\n")


# ─────────────────────────────────────────────
# Import Command
# ─────────────────────────────────────────────

def cmd_import(args):
    """Import instincts from file or URL."""
    source = args.source

    if source.startswith('http://') or source.startswith('https://'):
        print(f"Fetching from URL: {source}")
        try:
            with urllib.request.urlopen(source) as response:
                content = response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            return 1
    else:
        path = Path(source).expanduser()
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1
        content = path.read_text()

    new_instincts = parse_instinct_file(content)
    if not new_instincts:
        print("No valid instincts found in source.")
        return 1

    print(f"\nFound {len(new_instincts)} instincts to import.\n")

    existing = load_all_instincts()
    existing_ids = {i.get('id') for i in existing}

    to_add = []
    duplicates = []
    to_update = []

    for inst in new_instincts:
        inst_id = inst.get('id')
        if inst_id in existing_ids:
            existing_inst = next((e for e in existing if e.get('id') == inst_id), None)
            if existing_inst:
                if inst.get('confidence', 0) > existing_inst.get('confidence', 0):
                    to_update.append(inst)
                else:
                    duplicates.append(inst)
        else:
            to_add.append(inst)

    min_conf = args.min_confidence or 0.0
    to_add = [i for i in to_add if i.get('confidence', 0.5) >= min_conf]
    to_update = [i for i in to_update if i.get('confidence', 0.5) >= min_conf]

    if to_add:
        print(f"NEW ({len(to_add)}):")
        for inst in to_add:
            print(f"  + {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if to_update:
        print(f"\nUPDATE ({len(to_update)}):")
        for inst in to_update:
            print(f"  ~ {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if duplicates:
        print(f"\nSKIP ({len(duplicates)} - already exists with equal/higher confidence):")
        for inst in duplicates[:5]:
            print(f"  - {inst.get('id')}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return 0

    if not to_add and not to_update:
        print("\nNothing to import.")
        return 0

    if not args.force:
        response = input(f"\nImport {len(to_add)} new, update {len(to_update)}? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    source_name = Path(source).stem if not source.startswith('http') else 'web-import'
    output_file = INHERITED_DIR / f"{source_name}-{timestamp}.yaml"

    all_to_write = to_add + to_update
    output_content = f"# Imported from {source}\n# Date: {datetime.now().isoformat()}\n\n"

    for inst in all_to_write:
        output_content += "---\n"
        output_content += f"id: {inst.get('id')}\n"
        output_content += f"trigger: \"{inst.get('trigger', 'unknown')}\"\n"
        output_content += f"confidence: {inst.get('confidence', 0.5)}\n"
        output_content += f"domain: {inst.get('domain', 'general')}\n"
        output_content += f"source: inherited\n"
        output_content += f"imported_from: \"{source}\"\n"
        if inst.get('source_repo'):
            output_content += f"source_repo: {inst.get('source_repo')}\n"
        output_content += "---\n\n"
        output_content += inst.get('content', '') + "\n\n"

    output_file.write_text(output_content)

    print(f"\n✅ Import complete!")
    print(f"   Added: {len(to_add)}")
    print(f"   Updated: {len(to_update)}")
    print(f"   Saved to: {output_file}")

    return 0


# ─────────────────────────────────────────────
# Export Command
# ─────────────────────────────────────────────

def cmd_export(args):
    """Export instincts to file."""
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts to export.")
        return 1

    if args.domain:
        instincts = [i for i in instincts if i.get('domain') == args.domain]

    if args.min_confidence:
        instincts = [i for i in instincts if i.get('confidence', 0.5) >= args.min_confidence]

    if not instincts:
        print("No instincts match the criteria.")
        return 1

    output = f"# Instincts export\n# Date: {datetime.now().isoformat()}\n# Total: {len(instincts)}\n\n"

    for inst in instincts:
        output += "---\n"
        for key in ['id', 'trigger', 'confidence', 'domain', 'source', 'source_repo']:
            if inst.get(key):
                value = inst[key]
                if key == 'trigger':
                    output += f'{key}: "{value}"\n'
                else:
                    output += f"{key}: {value}\n"
        output += "---\n\n"
        output += inst.get('content', '') + "\n\n"

    if args.output:
        Path(args.output).write_text(output)
        print(f"Exported {len(instincts)} instincts to {args.output}")
    else:
        print(output)

    return 0


# ─────────────────────────────────────────────
# Evolve Command
# ─────────────────────────────────────────────

def cmd_evolve(args):
    """Analyze instincts and suggest evolutions to skills/commands/agents."""
    instincts = load_all_instincts()

    if len(instincts) < 3:
        print("Need at least 3 instincts to analyze patterns.")
        print(f"Currently have: {len(instincts)}")
        return 1

    print(f"\n{'='*60}")
    print(f"  EVOLVE ANALYSIS - {len(instincts)} instincts")
    print(f"{'='*60}\n")

    high_conf = [i for i in instincts if i.get('confidence', 0) >= 0.8]
    print(f"High confidence instincts (>=80%): {len(high_conf)}")

    trigger_clusters = defaultdict(list)
    for inst in instincts:
        trigger = inst.get('trigger', '')
        trigger_key = trigger.lower()
        for keyword in ['when', 'creating', 'writing', 'adding', 'implementing', 'testing']:
            trigger_key = trigger_key.replace(keyword, '').strip()
        trigger_clusters[trigger_key].append(inst)

    skill_candidates = []
    for trigger, cluster in trigger_clusters.items():
        if len(cluster) >= 2:
            avg_conf = sum(i.get('confidence', 0.5) for i in cluster) / len(cluster)
            skill_candidates.append({
                'trigger': trigger,
                'instincts': cluster,
                'avg_confidence': avg_conf,
                'domains': list(set(i.get('domain', 'general') for i in cluster))
            })

    skill_candidates.sort(key=lambda x: (-len(x['instincts']), -x['avg_confidence']))

    print(f"\nPotential skill clusters found: {len(skill_candidates)}")

    if skill_candidates:
        print(f"\n## SKILL CANDIDATES\n")
        for i, cand in enumerate(skill_candidates[:5], 1):
            print(f"{i}. Cluster: \"{cand['trigger']}\"")
            print(f"   Instincts: {len(cand['instincts'])}")
            print(f"   Avg confidence: {cand['avg_confidence']:.0%}")
            print(f"   Domains: {', '.join(cand['domains'])}")
            print(f"   Instincts:")
            for inst in cand['instincts'][:3]:
                print(f"     - {inst.get('id')}")
            print()

    workflow_instincts = [i for i in instincts if i.get('domain') == 'workflow' and i.get('confidence', 0) >= 0.7]
    if workflow_instincts:
        print(f"\n## COMMAND CANDIDATES ({len(workflow_instincts)})\n")
        for inst in workflow_instincts[:5]:
            trigger = inst.get('trigger', 'unknown')
            cmd_name = trigger.replace('when ', '').replace('implementing ', '').replace('a ', '')
            cmd_name = cmd_name.replace(' ', '-')[:20]
            print(f"  /{cmd_name}")
            print(f"    From: {inst.get('id')}")
            print(f"    Confidence: {inst.get('confidence', 0.5):.0%}")
            print()

    agent_candidates = [c for c in skill_candidates if len(c['instincts']) >= 3 and c['avg_confidence'] >= 0.75]
    if agent_candidates:
        print(f"\n## AGENT CANDIDATES ({len(agent_candidates)})\n")
        for cand in agent_candidates[:3]:
            agent_name = cand['trigger'].replace(' ', '-')[:20] + '-agent'
            print(f"  {agent_name}")
            print(f"    Covers {len(cand['instincts'])} instincts")
            print(f"    Avg confidence: {cand['avg_confidence']:.0%}")
            print()

    if args.generate:
        generated = _generate_evolved(skill_candidates, workflow_instincts, agent_candidates)
        if generated:
            print(f"\n✅ Generated {len(generated)} evolved structures:")
            for path in generated:
                print(f"   {path}")
        else:
            print("\nNo structures generated (need higher-confidence clusters).")

    print(f"\n{'='*60}\n")
    return 0


def _generate_evolved(skill_candidates: list, workflow_instincts: list, agent_candidates: list) -> list[str]:
    """Generate skill/command/agent files from analyzed instinct clusters."""
    generated = []

    for cand in skill_candidates[:5]:
        trigger = cand['trigger'].strip()
        if not trigger:
            continue
        name = re.sub(r'[^a-z0-9]+', '-', trigger.lower()).strip('-')[:30]
        if not name:
            continue

        skill_dir = EVOLVED_DIR / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        content = f"# {name}\n\n"
        content += f"Evolved from {len(cand['instincts'])} instincts "
        content += f"(avg confidence: {cand['avg_confidence']:.0%})\n\n"
        content += f"## When to Apply\n\n"
        content += f"Trigger: {trigger}\n\n"
        content += f"## Actions\n\n"
        for inst in cand['instincts']:
            inst_content = inst.get('content', '')
            action_match = re.search(r'## Action\s*\n\s*(.+?)(?:\n\n|\n##|$)', inst_content, re.DOTALL)
            action = action_match.group(1).strip() if action_match else inst.get('id', 'unnamed')
            content += f"- {action}\n"

        (skill_dir / "SKILL.md").write_text(content)
        generated.append(str(skill_dir / "SKILL.md"))

    for inst in workflow_instincts[:5]:
        trigger = inst.get('trigger', 'unknown')
        cmd_name = re.sub(r'[^a-z0-9]+', '-', trigger.lower().replace('when ', '').replace('implementing ', ''))
        cmd_name = cmd_name.strip('-')[:20]
        if not cmd_name:
            continue

        cmd_file = EVOLVED_DIR / "commands" / f"{cmd_name}.md"
        content = f"# {cmd_name}\n\n"
        content += f"Evolved from instinct: {inst.get('id', 'unnamed')}\n"
        content += f"Confidence: {inst.get('confidence', 0.5):.0%}\n\n"
        content += inst.get('content', '')

        cmd_file.write_text(content)
        generated.append(str(cmd_file))

    for cand in agent_candidates[:3]:
        trigger = cand['trigger'].strip()
        agent_name = re.sub(r'[^a-z0-9]+', '-', trigger.lower()).strip('-')[:20]
        if not agent_name:
            continue

        agent_file = EVOLVED_DIR / "agents" / f"{agent_name}.md"
        domains = ', '.join(cand['domains'])
        instinct_ids = [i.get('id', 'unnamed') for i in cand['instincts']]

        content = f"---\nmodel: sonnet\ntools: Read, Grep, Glob\n---\n"
        content += f"# {agent_name}\n\n"
        content += f"Evolved from {len(cand['instincts'])} instincts "
        content += f"(avg confidence: {cand['avg_confidence']:.0%})\n"
        content += f"Domains: {domains}\n\n"
        content += f"## Source Instincts\n\n"
        for iid in instinct_ids:
            content += f"- {iid}\n"

        agent_file.write_text(content)
        generated.append(str(agent_file))

    return generated


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Instinct CLI for Instinct-Learning Plugin')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    status_parser = subparsers.add_parser('status', help='Show instinct status')

    import_parser = subparsers.add_parser('import', help='Import instincts')
    import_parser.add_argument('source', help='File path or URL')
    import_parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    import_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    import_parser.add_argument('--min-confidence', type=float, help='Minimum confidence threshold')

    export_parser = subparsers.add_parser('export', help='Export instincts')
    export_parser.add_argument('--output', '-o', help='Output file')
    export_parser.add_argument('--domain', help='Filter by domain')
    export_parser.add_argument('--min-confidence', type=float, help='Minimum confidence')

    evolve_parser = subparsers.add_parser('evolve', help='Analyze and evolve instincts')
    evolve_parser.add_argument('--generate', action='store_true', help='Generate evolved structures')

    args = parser.parse_args()

    if args.command == 'status':
        return cmd_status(args)
    elif args.command == 'import':
        return cmd_import(args)
    elif args.command == 'export':
        return cmd_export(args)
    elif args.command == 'evolve':
        return cmd_evolve(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
```

**Step 2: Make executable**

```bash
chmod +x /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/scripts/instinct_cli.py
```

**Step 3: Commit**

```bash
git add plugins/instinct-learning/scripts/instinct_cli.py
git commit -m "feat: add instinct_cli.py for instinct-learning plugin"
```

---

## Task 13: Update Plugin Manifest

**Files:**
- Modify: `plugins/instinct-learning/.claude-plugin/plugin.json`

**Step 1: Update plugin.json**

```json
{
  "name": "instinct-learning",
  "version": "2.0.0",
  "description": "Instinct-based learning plugin that observes your sessions, learns atomic behaviors with confidence scoring, and evolves them into skills/commands/agents",
  "author": {
    "name": "zhengyu.li",
    "email": "zhengyu.li@users.noreply.github.com"
  },
  "repository": "https://github.com/zhengyuli/oh-my-claude-code",
  "license": "MIT",
  "keywords": ["learning", "patterns", "observation", "evolution", "productivity"],
  "commands": ["commands/analyze.md", "commands/status.md", "commands/evolve.md", "commands/export.md", "commands/import.md"],
  "agents": ["agents/observer.md"],
  "hooks": "hooks/hooks.json"
}
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/.claude-plugin/plugin.json
git commit -m "feat: update plugin.json for v2.0.0"
```

---

## Task 14: Create README

**Files:**
- Create: `plugins/instinct-learning/README.md`

**Step 1: Write README.md**

```markdown
# Instinct-Learning Plugin

An instinct-based learning system that observes your Claude Code sessions, learns atomic behaviors with confidence scoring, and evolves them into skills/commands/agents.

## Features

- **Hook-based Observation**: Captures 100% of tool use events via PreToolUse/PostToolUse hooks
- **Manual Analysis**: Trigger pattern analysis on-demand with `/instinct:analyze`
- **Confidence Scoring**: Each instinct has a confidence score (0.3-0.9) based on observation frequency
- **Evolution**: Cluster related instincts into skills, commands, or agents
- **Import/Export**: Share instincts with your team

## Installation

Install from the oh-my-claude-code marketplace.

## Commands

| Command | Description |
|---------|-------------|
| `/instinct:analyze` | Analyze observations and create/update instincts |
| `/instinct:status` | Show all instincts with confidence scores |
| `/instinct:evolve` | Cluster instincts into skills/commands/agents |
| `/instinct:export` | Export instincts for sharing |
| `/instinct:import <file>` | Import instincts from others |

## Data Directory

```
~/.claude/instinct-learning/
├── config.json           # User configuration
├── observations.jsonl    # Observation data
├── instincts/
│   ├── personal/         # Auto-learned instincts
│   └── inherited/        # Imported instincts
└── evolved/
    ├── agents/           # Evolved agents
    ├── skills/           # Evolved skills
    └── commands/         # Evolved commands
```

## Instinct File Format

```markdown
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.65
domain: "workflow"
source: "session-observation"
created: "2026-02-28T10:30:00Z"
evidence_count: 8
---

# Prefer Grep Before Edit

## Action
Always use Grep to find the exact location before using Edit.

## Evidence
- Observed 8 times in session abc123
- Pattern: Grep → Read → Edit sequence
```

## Configuration

Edit `~/.claude/instinct-learning/config.json` to customize:

```json
{
  "observation": {
    "enabled": true,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate"]
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7
  },
  "evolution": {
    "cluster_threshold": 3
  }
}
```

## How It Works

1. **Capture**: Hooks automatically capture tool use events
2. **Analyze**: Run `/instinct:analyze` to detect patterns
3. **Learn**: Instincts are created with confidence scores
4. **Evolve**: Run `/instinct:evolve` to cluster into capabilities

## Privacy

- Observations stay local on your machine
- Only instincts (patterns) can be exported
- No actual code or conversation content is shared
```

**Step 2: Commit**

```bash
git add plugins/instinct-learning/README.md
git commit -m "docs: add README for instinct-learning plugin v2"
```

---

## Task 15: Final Verification

**Step 1: Verify directory structure**

```bash
find /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning -type f | sort
```

Expected output:
```
plugins/instinct-learning/.claude-plugin/plugin.json
plugins/instinct-learning/agents/observer.md
plugins/instinct-learning/commands/analyze.md
plugins/instinct-learning/commands/evolve.md
plugins/instinct-learning/commands/export.md
plugins/instinct-learning/commands/import.md
plugins/instinct-learning/commands/status.md
plugins/instinct-learning/config.schema.json
plugins/instinct-learning/hooks/hooks.json
plugins/instinct-learning/hooks/observe.sh
plugins/instinct-learning/README.md
plugins/instinct-learning/scripts/instinct_cli.py
```

**Step 2: Test CLI**

```bash
python3 /Users/zhengyuli/oh-my-claude-code/plugins/instinct-learning/scripts/instinct_cli.py status
```

Expected: Shows "No instincts found." with directory paths

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete instinct-learning plugin v2.0.0 refactor"
```
