# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the instinct-learning plugin.

## Common Issues

### "No observations file found"

**Cause**: Observations directory doesn't exist or no hooks have run.

**Solution**:
1. Run some Claude Code commands to generate observations (Edit, Read, Grep, etc.)
2. Check that hooks are enabled:
   ```bash
   ls ~/.claude/instinct-learning/disabled 2>/dev/null
   # If this file exists, hooks are disabled
   rm ~/.claude/instinct-learning/disabled  # Re-enable hooks
   ```
3. Verify hooks are configured:
   ```bash
   cat ~/.claude/plugins/instinct-learning/hooks/hooks.json
   ```

### "Instincts not being created"

**Cause**: Analyzer agent may not have relevant patterns or insufficient observations.

**Solution**:
1. Check observation count:
   ```bash
   ls -la ~/.claude/instinct-learning/observations/
   ```
2. Ensure you have 10+ archived observations before running `/instinct:analyze`
3. Active observations file hasn't been archived yet - wait for more activity
4. Check analyzer agent output for pattern detection results

### "Evolve produces no results"

**Cause**: Insufficient instincts or low confidence scores.

**Solution**:
1. Check instinct count:
   ```bash
   /instinct:status
   ```
2. Minimum requirements:
   - At least 3 instincts
   - Confidence >= 0.6 for meaningful clustering
3. Run `/instinct:analyze` to create more instincts
4. Check if instincts have high enough confidence

### "Race conditions" warning

**Cause**: Multiple hooks trying to rotate files simultaneously.

**Solution**:
1. The flock-based locking in observe.sh prevents this
2. If issues persist, check lock file:
   ```bash
   ls -la ~/.claude/instinct-learning/observations/.lock
   ```
3. Stale lock files should be cleaned up automatically

### "Permission denied" errors

**Cause**: Data directory permissions or file access issues.

**Solution**:
1. Check directory permissions:
   ```bash
   ls -la ~/.claude/instinct-learning/
   ```
2. Fix permissions if needed:
   ```bash
   chmod -R 755 ~/.claude/instinct-learning/
   ```
3. Ensure DATA_DIR is writable:
   ```bash
   touch ~/.claude/instinct-learning/test && rm ~/.claude/instinct-learning/test
   ```

## Debug Mode

Enable debug logging for hooks:

```bash
export DEBUG_HOOKS=1
# Run your commands
unset DEBUG_HOOKS
```

Debug output will show:
- Hook execution start
- Lock acquisition status
- Observation file path
- Write confirmation

## Data Directory Issues

### Using custom data directory

If `INSTINCT_LEARNING_DATA_DIR` is set:

```bash
export INSTINCT_LEARNING_DATA_DIR=/custom/path
# Verify it's being used
ls $INSTINCT_LEARNING_DATA_DIR/observations/
```

**Note**: All modules (hooks, agents, CLI) respect this variable.

### Moving data directory

1. Stop all Claude Code sessions
2. Copy existing data:
   ```bash
   cp -r ~/.claude/instinct-learning /new/location
   ```
3. Set environment variable:
   ```bash
   export INSTINCT_LEARNING_DATA_DIR=/new/location/instinct-learning
   ```
4. Verify:
   ```bash
   /instinct:status
   ```

## Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| E001 | Observations directory missing | Run commands to generate data |
| E002 | No instincts found | Run `/instinct:analyze` |
| E003 | Low confidence instincts | More observations needed |
| E004 | Lock timeout | Another process is writing |
| E005 | Permission denied | Check directory permissions |

## Hook Issues

### Hooks not capturing data

1. Verify hook configuration:
   ```bash
   cat ~/.claude/plugins/instinct-learning/hooks/hooks.json
   ```
2. Check if hooks are disabled:
   ```bash
   ls ~/.claude/instinct-learning/disabled
   ```
3. Test hook manually:
   ```bash
   echo '{"hook_type":"PostToolUse","tool_name":"Test"}' | bash ~/.claude/plugins/instinct-learning/hooks/observe.sh post
   ```
4. Check observations file:
   ```bash
   tail -f ~/.claude/instinct-learning/observations/observations.jsonl
   ```

### Hook execution failures

1. Enable DEBUG_HOOKS to see detailed error messages
2. Check hook script syntax:
   ```bash
   bash -n ~/.claude/plugins/instinct-learning/hooks/observe.sh
   ```
3. Verify required tools are available:
   ```bash
   which python3 bash
   ```
4. Test with valid JSON input

## Agent Issues

### Analyzer agent not finding patterns

1. Check archived observations:
   ```bash
   ls -la ~/.claude/instinct-learning/observations/observations.*.jsonl
   ```
2. Active file isn't processed - wait for rotation or manual trigger
3. Minimum 10 observations needed for meaningful patterns
4. Check agent logs for specific errors

### Evolver agent not creating artifacts

1. Verify instinct count and confidence:
   ```bash
   /instinct:status --min-confidence 0.6
   ```
2. Check evolved directories:
   ```bash
   ls -la ~/.claude/instinct-learning/evolved/
   ```
3. 50-item limit may be preventing new artifacts
4. Low confidence instincts (< 0.6) won't be evolved

## Performance Issues

### Large observation files

- Files > 2MB are automatically rotated
- Archives are cleaned after analysis
- Configure limits in observe.sh:
  ```bash
  MAX_FILE_SIZE_MB=2  # Rotation threshold
  MAX_ARCHIVE_FILES=10  # Max archives to keep
  ```

### Slow hook execution

- Hook runs asynchronously (non-blocking)
- Enable DEBUG_HOOKS to measure timing
- Consider reducing observation frequency

## Getting Help

If you encounter issues not covered here:

1. Check test status:
   ```bash
   ./tests/run_all.sh
   ```
2. Review test output for specific errors
3. Enable debug logging for detailed traces
4. Check git log for recent changes:
   ```bash
   git log --oneline -10
   ```

## Recovery Procedures

### Corrupted observations file

1. Stop using the plugin
2. Backup existing data:
   ```bash
   cp -r ~/.claude/instinct-learning ~/.claude/instinct-learning.backup
   ```
3. Remove corrupted file:
   ```bash
   rm ~/.claude/instinct-learning/observations/observations.jsonl
   ```
4. Restart - hooks will create new file

### Lost instincts

1. Check archived directory:
   ```bash
   ls ~/.claude/instinct-learning/instincts/archived/
   ```
2. Import from backup if available
3. Instincts are created from observations - re-run analysis

### Reset to clean state

```bash
# WARNING: This deletes all data
rm -rf ~/.claude/instinct-learning
# Plugin will recreate directories on next use
```
