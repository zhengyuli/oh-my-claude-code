# Architecture

This document describes the architecture of the instinct-learning plugin.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude Code Main Session                    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Hooks Layer (100% reliable, non-blocking)                       │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  PreToolUse      │    │  PostToolUse     │                   │
│  │  Records start   │    │  Records result  │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                      ┌──────────────────┐                       │
│                      │  Stop            │                       │
│                      │  Session cleanup │                       │
│                      └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  observations.jsonl (JSONL format)                               │
│  One observation per line, append-only                           │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Observer Agent (Background, Haiku model)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Load observations from JSONL                         │   │
│  │  2. Detect patterns (sequences, error-fix, preferences)  │   │
│  │  3. Calculate confidence scores                          │   │
│  │  4. Create/update instinct files                         │   │
│  │  5. Flag evolution opportunities                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Instincts Store (YAML frontmatter + Markdown)                   │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  personal/       │    │  shared/         │                   │
│  │  Auto-learned    │    │  Imported        │                   │
│  └──────────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Evolution Engine (User-triggered via /instinct:evolve)          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Skills   │  │Commands  │  │ Agents   │                       │
│  │Auto-apply│  │User-call │  │Specialist│                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Hooks Layer

The hooks are the entry point for all observation capture. They are:

- **Non-blocking**: Run asynchronously in background
- **Fail-safe**: Always exit 0, never interrupt the main session
- **Configurable**: Can filter which tools to observe

#### PreToolUse Hook (`hooks/pre-tool.sh`)
- Fires before any tool execution
- Records: timestamp, tool name, session ID, input (truncated)

#### PostToolUse Hook (`hooks/post-tool.sh`)
- Fires after tool execution completes
- Records: timestamp, tool name, exit code, response (truncated)

#### Stop Hook (`hooks/stop.sh`)
- Fires when session ends
- Updates session statistics
- Archives old observations if needed

### 2. Observation Storage

Observations are stored in JSONL format (one JSON object per line):

```json
{"timestamp":"2025-01-15T10:30:00Z","type":"pre_tool","tool":"Edit","session":"abc123"}
{"timestamp":"2025-01-15T10:30:05Z","type":"post_tool","tool":"Edit","exit_code":"0","session":"abc123"}
```

Benefits of JSONL:
- Append-only (no file locking issues)
- Streamable (can process while writing)
- Line-oriented (easy to parse)

### 3. Observer Agent

The observer agent runs in the background (default: every 5 minutes) and:

1. **Loads Observations**: Reads from JSONL file
2. **Detects Patterns**:
   - Repeated sequences (3+ occurrences)
   - Error-fix patterns (failure followed by recovery)
   - Tool preferences (dominant tool usage)
   - Domain patterns (categorized by tool types)
3. **Calculates Confidence**: Based on occurrence count, consistency, corrections
4. **Creates/Updates Instincts**: Writes to personal/ directory

### 4. Instinct Storage

Instincts use YAML frontmatter + Markdown format:

```markdown
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
created: "2025-01-15T10:30:00Z"
source: "observation"
evidence_count: 5
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed in 5 different sessions
- User consistently uses map/filter/reduce
```

### 5. Evolution Engine

Triggered by `/instinct:evolve` command:

1. **Groups by Domain**: Organizes instincts by category
2. **Detects Clusters**: Finds domains with 3+ instincts, avg confidence ≥ 0.7
3. **Determines Type**:
   - **Skill**: Auto-triggered (keywords: when, always, automatically)
   - **Command**: User-invoked (keywords: run, execute, perform)
   - **Agent**: Complex tasks (keywords: analyze, research, investigate)
4. **Generates Capability**: Creates appropriate file in evolved/

### 6. Session Management

Tracks session statistics:
- Total session count
- Last session timestamp
- Observation count
- Instinct evolution status

## Data Flow

```
User Action → Tool Execution → Hook Fires → Observation Written
                                                    │
                                                    ▼
                                            JSONL File
                                                    │
                                                    ▼
Observer Agent (background) ──────────────► Pattern Detection
                                                    │
                                                    ▼
                                            Instinct Created
                                                    │
                                                    ▼
User runs /evolve ────────────────────────► Clustering
                                                    │
                                                    ▼
                                            Capability Generated
```

## Configuration

Configuration is stored in `~/.claude/instinct-learning/config.json`:

```json
{
  "observation": {
    "enabled": true,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate", "TaskList"],
    "max_prompt_length": 500,
    "max_response_length": 1000,
    "max_file_size_mb": 10,
    "archive_after_days": 7
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts_per_domain": 20
  },
  "observer": {
    "enabled": true,
    "model": "haiku",
    "run_interval_minutes": 5
  },
  "evolution": {
    "cluster_threshold": 3,
    "min_avg_confidence": 0.7
  }
}
```

## Error Handling

All components follow the "never fail" principle:

- Hooks always exit 0
- Observer logs errors but continues
- CLI provides graceful error messages
- Invalid observations are skipped, not crash

## Performance Considerations

- **Hooks**: Async execution, minimal overhead (~10ms)
- **Observer**: Runs at configurable intervals, uses Haiku for cost efficiency
- **Storage**: JSONL is append-only, no locking needed
- **Archiving**: Automatic when files exceed size threshold
