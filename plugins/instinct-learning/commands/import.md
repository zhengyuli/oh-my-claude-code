---
name: instinct:import
description: Import instincts from file or URL
---

# Import Instincts

Import instincts shared by others or restore from backup.

## Process

1. **Load Source**: Read from:
   - Local file path
   - HTTP/HTTPS URL

2. **Parse Instincts**: Extract from YAML frontmatter + Markdown format

3. **Handle Duplicates**:
   - `--merge`: Update existing, add new (default)
   - Without merge: Add all to shared/

4. **Mark Source**: Tag as `imported` for tracking

## Usage Examples

Import from local file:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py import ~/Downloads/team-instincts.md
```

Import from URL:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py import https://example.com/instincts/testing-patterns.md
```

Import with merge:
```bash
python3 ~/.claude/plugins/instinct-learning/scripts/instinct-cli.py import team-instincts.md --merge
```

## Import Behavior

### Without --merge
- All instincts go to `shared/` directory
- Existing instincts are preserved
- Duplicates get new IDs

### With --merge
- Matching triggers update existing instincts
- Confidence is averaged
- Evidence is combined
- New instincts added to `shared/`

## Output

```
Importing from: team-instincts.md
Parsing instincts...
Found 12 instincts

  ✓ prefer-functional-style (updated)
  ✓ always-test-first (new)
  ✓ commit-often (new)
  ...

Imported 12 instincts to shared/
  - 3 updated existing
  - 9 new additions
```

## URL Support

Supports importing from:
- GitHub raw URLs
- Gist URLs
- Any direct markdown file URL

The URL must return content in the expected YAML frontmatter + Markdown format.
