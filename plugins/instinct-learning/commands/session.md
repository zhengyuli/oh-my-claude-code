---
name: instinct:session
description: Manage session tracking and view statistics
---

# Session Management

View session statistics and manage session memory.

## Process

1. **Load Session Data**: Read from `~/.claude/instinct-learning/session.json`
2. **Display Statistics**: Show session count and history
3. **Session Memory**: Optionally clear or export session context

## Usage

View session statistics:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py session --stats
```

## Output

```
📊 Session Statistics

Total sessions: 47
Last session: 2025-01-15T14:30:00Z

Learning Progress:
  Observations: 1,234
  Instincts: 23
  Evolved: 3 skills, 1 command

Session Streak: 5 days
```

## Session Memory Skill

The session-memory skill automatically loads at session start to provide:
- Session count
- Recent learnings
- Evolution opportunities
- Quick stats

See `/skill:session-memory` for details.

## Data Storage

Session data is stored in:
```
~/.claude/instinct-learning/
├── session.json           # Session count and timestamps
├── observations.jsonl     # Current session observations
└── observations.archive/  # Archived observation logs
```

## Archive Management

Observations are automatically archived when:
- File size exceeds configured limit (default: 10MB)
- Session ends (via Stop hook)

Archives are cleaned up after:
- Configured retention period (default: 7 days)
