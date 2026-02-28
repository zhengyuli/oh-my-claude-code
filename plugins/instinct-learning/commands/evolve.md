---
name: instinct:evolve
description: Cluster related instincts and generate skills/commands/agents
---

# Evolve Instincts into Capabilities

Analyze all instincts and propose evolution into higher-level capabilities: skills, commands, or agents.

## Process

1. **Load Instincts**: Read all instincts from personal and shared directories

2. **Group by Domain**: Organize instincts by their domain category:
   - code-style
   - testing
   - git
   - debugging
   - workflow
   - architecture
   - documentation

3. **Detect Clusters**: Find domains with:
   - 3+ instincts
   - Average confidence ≥ 0.7

4. **Determine Capability Type**:
   - **Skill**: Auto-triggered behaviors (when X happens, do Y)
   - **Command**: User-invoked tasks (run /do-something)
   - **Agent**: Deep specialists requiring isolation

5. **Generate Proposals**: For each cluster, propose:
   - Name and description
   - Type determination
   - Merged actions
   - Trigger conditions

6. **Confirm and Create**: Ask user to confirm each generation

## Output Format

For each cluster found:

```
Domain: testing-workflow
Instincts: 5 (avg confidence: 0.78)
Proposed: Skill
Actions:
  - Write tests before code
  - Use TDD cycle
  - Run tests after each change
  - Mock external dependencies
  - Test edge cases

Generate this skill? (y/n/e=edit)
```

## Capability Generation

When confirmed, generate appropriate files:

### Skill
Creates `~/.claude/instinct-learning/evolved/skills/<name>.md`

### Command
Creates `~/.claude/instinct-learning/evolved/commands/<name>.md`

### Agent
Creates `~/.claude/instinct-learning/evolved/agents/<name>.md`

## Actions

Execute the evolve command:

```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py evolve --generate
```

Use `--dry-run` to see proposals without generating files.
