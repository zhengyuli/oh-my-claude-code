# Instinct-Learning Plugin Architecture

This document provides a comprehensive overview of the instinct-learning plugin's architecture, design decisions, and component interactions.

## Table of Contents

- [Overview](#overview)
- [Design Philosophy](#design-philosophy)
- [System Architecture](#system-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Technical Specifications](#technical-specifications)
- [Extension Points](#extension-points)
- [Performance Considerations](#performance-considerations)

## Overview

The instinct-learning plugin is a **three-stage learning pipeline** that:

1. **Observes** Claude Code sessions via non-blocking hooks
2. **Analyzes** observations to detect patterns using AI
3. **Evolves** patterns into reusable artifacts (skills, commands, agents)

### Key Characteristics

- **Async-first**: Hooks never block session activity
- **AI-powered**: Pattern detection using Claude Haiku for cost efficiency
- **Confidence-based**: Actions weighted by statistical confidence
- **Privacy-first**: Observations stored locally, only patterns exportable
- **Fail-safe**: All components handle errors gracefully

## Design Philosophy

### Separation of Concerns

Each component has a single, well-defined responsibility:

```
Hooks → Data Capture
Analyzer → Pattern Detection
Evolver → Artifact Generation
CLI → Data Management
```

### Immutability

Observations are **never modified** once written:
- Observations are append-only (JSONL format)
- Archives are numbered, never rotated in-place
- Instincts reference observations by immutable IDs

### Non-Blocking Operations

All user-facing operations are non-blocking:
- Hooks execute asynchronously in background
- Agent operations use appropriate model tiers
- CLI operations provide progress feedback

### Graceful Degradation

The system continues to function even when components fail:
- Hook failures don't interrupt sessions
- Missing observations trigger warnings, not errors
- Partial analysis results are still useful

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code Session                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Hook Layer (observe.sh)                      │
│  • PreToolUse: Capture tool invocation                          │
│  • PostToolUse: Capture tool result                            │
│  • Stop: Capture session end                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Observation Storage (JSONL)                   │
│  • data/observations/observations.jsonl                        │
│  • data/archive/observations.{timestamp}.jsonl                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
         ┌──────────────────┐         ┌──────────────────┐
         │  Manual Trigger  │         │  CLI Access      │
         │  /instinct:analyze│        │  instinct-cli    │
         └──────────────────┘         └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Analysis Layer (Analyzer Agent)                    │
│  • Pattern detection (Haiku model)                              │
│  • Confidence scoring (0.3-0.9)                                 │
│  • Domain categorization                                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│               Instinct Storage (YAML + MD)                      │
│  • data/instincts/personal/{id}.md                             │
│  • Frontmatter: metadata                                        │
│  • Content: trigger, action, evidence                           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
         ┌──────────────────┐         ┌──────────────────┐
         │  CLI Access      │         │  Manual Trigger  │
         │  instinct-cli    │         │  /instinct:evolve │
         └──────────────────┘         └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Evolution Layer (Evolver Agent)                    │
│  • Semantic clustering (Sonnet model)                           │
│  • Artifact type determination                                 │
│  • Merge and prune strategies                                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
         ┌──────────────────┐         ┌──────────────────┐
         │  Evolved Skills  │         │  Evolved Agents  │
         │  evolved/skills/ │         │  evolved/agents/ │
         └──────────────────┘         └──────────────────┘
```

## Component Details

### 1. Hook Layer

#### observe.sh

**Purpose**: Capture session activity without blocking

**Key Features**:
- Atomic mkdir-based locking (portable across macOS/Linux)
- Numbered archive rotation (observations.{timestamp}.jsonl)
- Input truncation (1000 chars) to prevent bloat
- Race condition prevention (-mmin +5 for cleanup)
- Debug mode support (DEBUG_HOOKS env var)

**Design Decisions**:

| Decision | Rationale |
|----------|-----------|
| Async execution | Hooks must never interrupt sessions |
| mkdir-based locking | More portable than flock across platforms |
| JSONL format | Append-only, easy to parse, supports streaming |
| 1000 char truncation | Balance between context and storage efficiency |
| Numbered archives | Prevent data loss, enable time-based queries |

**Error Handling**:
- Lock timeout: 5 seconds with retry
- JSON parsing failures: Logged, skipped
- Write failures: Logged, session continues

### 2. Observation Storage

#### Schema

```json
{
  "timestamp": "2025-02-28T12:00:00Z",
  "event_type": "PreToolUse|PostToolUse|Stop",
  "tool_name": "Edit|Write|Bash|Read|Grep|Glob",
  "tool_input": "...",
  "tool_result": "...",
  "session_id": "..."
}
```

#### Rotation Strategy

- Trigger: 1000 observations or 7 days
- Format: `observations.{timestamp}.jsonl`
- Retention: Configurable (default: 30 days)

### 3. Analyzer Agent

#### Purpose

Detect patterns in archived observations and create instincts

#### Model Selection

**Haiku 3.5** (90% of Sonnet capability, 3x cost savings):
- Lightweight, high-frequency pattern detection
- Fast processing of large observation sets
- Cost-effective for repeated analysis

#### Pattern Detection Algorithms

1. **Repeated Sequences**: Actions that occur 3+ times in similar contexts
2. **Error→Fix Patterns**: Error followed by corrective action
3. **Tool Preferences**: Preferred tools for specific task types
4. **Workflow Patterns**: Common command sequences

#### Confidence Scoring

Formula: `base_score + (occurrence_count * 0.1) + consistency_bonus`

- Base score: 0.3 (minimum viable pattern)
- Occurrence multiplier: 0.1 per occurrence (max 0.5)
- Consistency bonus: 0.1 if context varies < 30%
- Range: 0.3 - 0.9

#### Pruning Strategy

Auto-prune instincts when count exceeds 100:
- Remove instincts with confidence < 0.4
- Merge instincts with similarity > 80%
- Keep minimum of 80 instincts (user config override)

### 4. Instinct Storage

#### File Format

```markdown
---
id: error-handling-rest-api
trigger: "when encountering HTTP errors from REST API calls"
confidence: 0.7
domain: "error-handling"
created: "2025-02-28T12:00:00Z"
source: "observation"
evidence_count: 5
---

# REST API Error Handling

## Trigger
When encountering HTTP errors (4xx, 5xx) from REST API calls

## Action
1. Check error status code
2. Parse response body for error details
3. Implement retry with exponential backoff for 5xx errors
4. Log error context for debugging
5. Return user-friendly error message

## Evidence
- 2025-02-27T10:15:00Z: Handled 429 rate limit with retry
- 2025-02-27T14:30:00Z: Implemented 500 error recovery
- 2025-02-28T09:00:00Z: Added error detail parsing
```

#### Domains

- `code-style`: Coding patterns and preferences
- `testing`: Test writing and execution patterns
- `git`: Version control workflows
- `debugging`: Error investigation and fixing
- `workflow`: General development workflow
- `architecture`: System design decisions
- `documentation`: Documentation patterns

### 5. Evolver Agent

#### Purpose

Transform instincts into reusable artifacts via semantic clustering

#### Model Selection

**Sonnet 4.6** (Best coding model):
- Semantic clustering requires complex reasoning
- Understanding of code patterns and workflows
- Balance of capability and cost

#### Clustering Strategy

1. **Group by Domain**: Separate instincts by domain
2. **Semantic Similarity**: Cluster related instincts within domain
3. **Capability Determination**: Decide artifact type (skill/command/agent)
4. **Threshold Enforcement**: Only cluster 3+ instincts

#### Merge Criteria

| Condition | Action |
|-----------|--------|
| Confidence > 0.7, Similarity > 80% | Merge instincts |
| Confidence < 0.4 | Prune instinct |
| Count < 3 | Keep as individual instincts |

#### Artifact Type Determination

| Type | Criteria | Example |
|------|----------|---------|
| **Skill** | Single domain, actionable pattern | "Test-Driven Development" |
| **Command** | User-facing operation | `/git:commit-with-pr-template` |
| **Agent** | Multi-step reasoning required | "Code Review Agent" |

#### Nested Skills Structure

Skills are organized in nested directories:

```
evolved/skills/
├── development/
│   ├── tdd.md
│   ├── debugging.md
│   └── refactoring.md
├── git/
│   ├── commit-workflow.md
│   └── branch-management.md
└── testing/
    ├── unit-testing.md
    └── integration-testing.md
```

**Rationale**: Mirrors Claude Code's skill organization, improves discoverability

#### Prune Strategy

After clustering:
- Remove merged instincts from `data/instincts/personal/`
- Archive original instinct files
- Update observation references

### 6. CLI Layer

#### Commands

| Command | Purpose | Implementation |
|---------|---------|----------------|
| `status` | Display all instincts | CLI only (no agent) |
| `analyze` | Trigger analysis | Agent dispatch |
| `evolve` | Trigger evolution | Agent dispatch |
| `export` | Export instincts | CLI only |
| `import` | Import instincts | CLI only |
| `prune` | Remove low-confidence | CLI only |
| `decay` | Analyze confidence decay | CLI only |

#### Python Architecture

```
scripts/
├── instinct_cli.py      # Main entry point
├── cli_parser.py        # Argument parsing
├── commands/            # Command implementations
│   ├── status.py
│   ├── export.py
│   ├── import.py
│   ├── prune.py
│   └── decay.py
└── utils/               # Utility modules
    ├── confidence.py    # Confidence scoring
    ├── file_io.py       # File operations
    └── instinct_parser.py  # YAML parsing
```

## Data Flow

### Observation Flow

```
1. User invokes tool (e.g., Edit)
2. PreToolUse hook fires
3. observe.sh captures invocation (async, non-blocking)
4. Tool executes
5. PostToolUse hook fires
6. observe.sh captures result (async, non-blocking)
7. Session ends
8. Stop hook fires
9. observe.sh captures session end
10. Observations written to data/observations/observations.jsonl
11. After 1000 obs or 7 days, rotate to archive/
```

### Analysis Flow

```
1. User invokes /instinct:analyze OR instinct-cli analyze
2. Analyzer agent (Haiku) triggered
3. Agent reads archived observations
4. Agent detects patterns
5. Agent scores patterns (confidence)
6. Agent creates instinct files in data/instincts/personal/
7. If count > 100, agent prunes low-confidence instincts
8. Summary returned to user
```

### Evolution Flow

```
1. User invokes /instinct:evolve OR instinct-cli evolve
2. Evolver agent (Sonnet) triggered
3. Agent reads instincts from data/instincts/personal/
4. Agent groups by domain
5. Agent performs semantic clustering
6. Agent determines artifact types
7. Agent creates artifacts:
   - evolved/skills/{domain}/{name}.md
   - evolved/commands/{name}.md
   - evolved/agents/{name}.md
8. Agent merges and prunes instincts
9. Summary returned to user
```

## Design Decisions

### Decision 1: Async Hook Execution

**Problem**: Hooks must not block session activity

**Options**:
1. Synchronous execution (blocking)
2. Async background execution with wait
3. Async background execution with fire-and-forget

**Choice**: Option 3 - Fire-and-forget async

**Rationale**:
- Sessions should never wait for observation capture
- Lock contention should not interrupt user workflow
- Failed observations are acceptable, blocked sessions are not

### Decision 2: JSONL Format

**Problem**: Efficient storage and parsing of observations

**Options**:
1. Single JSON array file
2. Multiple JSON files (one per observation)
3. JSONL (newline-delimited JSON)

**Choice**: Option 3 - JSONL

**Rationale**:
- Append-only operations (no file rewriting)
- Streaming support (read line-by-line)
- Easy to parse with any language
- Standard format for log data

### Decision 3: Confidence Scoring Range

**Problem**: Define useful confidence range for instincts

**Options**:
1. 0.0 - 1.0 (full range)
2. 0.3 - 0.9 (practical range)
3. 1 - 100 (integer percentage)

**Choice**: Option 2 - 0.3 - 0.9

**Rationale**:
- 0.3 minimum: Pattern must occur at least 3 times
- 0.9 maximum: Cap to prevent false confidence
- Avoids 0.0-0.2 (noise) and 1.0 (impossible certainty)

### Decision 4: Manual Analysis Trigger

**Problem**: When to analyze observations

**Options**:
1. Automatic after every session
2. Automatic after N observations
3. Manual trigger only

**Choice**: Option 3 - Manual trigger

**Rationale**:
- Gives user control over when analysis occurs
- Avoids unexpected API costs
- Allows analysis at convenient times
- User can set up automated triggers if desired

### Decision 5: Model Selection

**Problem**: Balance capability and cost

**Options**:
1. Use Sonnet for everything
2. Use Haiku for everything
3. Tiered approach: Haiku for detection, Sonnet for evolution

**Choice**: Option 3 - Tiered approach

**Rationale**:
- Haiku sufficient for pattern detection (90% of Sonnet capability)
- Sonnet necessary for semantic clustering (complex reasoning)
- 3x cost savings for frequent operations
- Optimal capability-cost tradeoff

## Technical Specifications

### Filesystem Structure

```
~/.claude/instinct-learning/
├── config.json                 # User configuration
├── data/
│   ├── observations/
│   │   ├── observations.jsonl  # Current observations
│   │   └── archive/            # Archived observations
│   │       ├── observations.2025-02-21.jsonl
│   │       └── observations.2025-02-28.jsonl
│   ├── instincts/
│   │   ├── personal/           # User instincts
│   │   │   ├── error-handling-rest-api.md
│   │   │   └── tdd-workflow.md
│   │   └── imported/           # Imported instincts
│   ├── sessions/
│   │   └── {session_id}/       # Session data
│   └── evolved/
│       ├── skills/             # Evolved skills
│       │   ├── development/
│       │   ├── git/
│       │   └── testing/
│       ├── commands/           # Evolved commands
│       └── agents/             # Evolved agents
└── logs/
    ├── analyzer.log            # Analyzer agent logs
    ├── evolver.log             # Evolver agent logs
    └── hook.log                # Hook script logs
```

### Configuration Schema

```json
{
  "$schema": "./config.schema.json",
  "observation": {
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate"],
    "max_input_length": 1000,
    "archive_threshold": 1000,
    "archive_days": 7
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7,
    "max_count": 100
  },
  "evolution": {
    "cluster_threshold": 3,
    "merge_similarity": 0.8,
    "prune_confidence": 0.4
  },
  "data_dir": "~/.claude/instinct-learning/data"
}
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `INSTINCT_LEARNING_DATA_DIR` | Override data directory | `~/.claude/instinct-learning/data` |
| `DEBUG_HOOKS` | Enable hook debug logging | `unset` |
| `HOOK_DISABLED` | Disable all hooks | `unset` |

## Extension Points

### Adding New Domains

Edit `agents/analyzer.md`:
```markdown
### Domains

- `existing-domain`: Description
- `your-new-domain`: Description
```

### Adding New Pattern Types

Edit `agents/analyzer.md` pattern detection section:
```markdown
#### Your New Pattern Type

Description of pattern type

Detection criteria:
- Criterion 1
- Criterion 2
```

### Custom Confidence Scoring

Edit `scripts/utils/confidence.py`:
```python
def calculate_confidence(pattern: Pattern) -> float:
    # Custom scoring logic
    return confidence_score
```

### Adding New CLI Commands

1. Create `scripts/commands/your_command.py`
2. Register in `scripts/instinct_cli.py`
3. Add CLI parser in `scripts/cli_parser.py`

## Performance Considerations

### Scalability

| Component | Scalability Characteristics |
|-----------|---------------------------|
| Hooks | O(1) per observation, async, non-blocking |
| Observation Storage | O(n) write, O(1) append |
| Analyzer | O(n) where n = archived observations |
| Evolver | O(n²) clustering, limited to 50 instincts |

### Bottlenecks

1. **Observation Rotation**: Can delay session end (mitigated by async)
2. **Large Analysis Sets**: Haiku slower on >10k observations (mitigated by archival)
3. **Clustering Complexity**: Sonnet O(n²) (mitigated by 50-item limit)

### Optimization Strategies

1. **Incremental Analysis**: Only analyze new observations
2. **Cached Confidence**: Store confidence scores, recalc on change
3. **Lazy Loading**: Load observations on-demand for large sets
4. **Parallel Processing**: Process domains independently during evolution

---

**Document Version**: 1.0.0
**Last Updated**: 2025-02-28
**Maintainer**: Instinct-Learning Plugin Team
