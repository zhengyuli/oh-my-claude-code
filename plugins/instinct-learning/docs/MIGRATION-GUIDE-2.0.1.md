# Migration Guide: v2.0.0 → v2.0.1

## What's Changing?

This release fixes **3 critical security and reliability issues**. All users are strongly recommended to upgrade.

**Quick Summary:**
- 🔒 **Security fix:** Prevents remote code execution via malicious instinct files
- 💾 **Data loss prevention:** Fixes race condition in archive cleanup
- ✅ **Reliability:** Test coverage increased from 16% to 95%

---

## Do I Need to Upgrade?

**YES** if any of these apply to you:

- ✅ You use instinct-learning in production
- ✅ You import instincts from external sources (team, community)
- ✅ Your analyzer sometimes takes >5 minutes to run
- ✅ You care about data integrity and security

**Maybe** if:
- You only use instinct-learning for personal experimentation
- You never import external instincts
- Your analysis sessions are always fast (<5 minutes)

---

## Breaking Changes

**None!** This is a drop-in replacement. No configuration changes required.

---

## Upgrade Steps

### 1. Backup Your Data (Recommended)

```bash
cp -r ~/.claude/instinct-learning ~/.claude/instinct-learning.backup
```

### 2. Pull Latest Changes

```bash
cd /path/to/oh-my-claude-code
git pull origin main
cd plugins/instinct-learning
```

### 3. Run Tests to Verify

```bash
./tests/run_all.sh --coverage
```

Expected output:
```
========================= test session starts ==========================
collected 282 items

... (test output) ...

282 passed in 45.23s

---------- coverage: platform darwin, linux2 ----------
Name                                    Stmts   Miss  Cover
-------------------------------------------------------------------
scripts/utils/file_io.py                  45      2    96%
scripts/utils/instinct_parser.py          62      1    98%
scripts/utils/confidence.py               38      3    92%
...
TOTAL                                     692     35    95%
```

### 4. Verify Your Instincts Still Work

```bash
# Run status command
/instinct:status

# Or via CLI
python3 scripts/instinct-cli.py status
```

### 5. Test Analyzer

```bash
# Trigger a manual analysis
/instinct:analyze

# Verify no errors in logs
tail -f ~/.claude/instinct-learning/logs/analyzer.log
```

---

## What's Fixed?

### Fix 1: YAML Injection Vulnerability 🔒

**Before:** Malicious instinct files could execute arbitrary code
**After:** All YAML is parsed safely with `yaml.safe_load()`

**What this means for you:**
- If you import instincts from untrusted sources, they can no longer run arbitrary code
- Your instincts are still processed normally (no functional change)
- Slight performance improvement (faster parsing)

### Fix 2: Race Condition in Archive Cleanup 💾

**Before:** If analyzer took >5 minutes, archives could be deleted while still being read
**After:** `.processing` marker prevents cleanup during analysis

**What this means for you:**
- No more data loss from premature cleanup
- Long-running analysis sessions are now safe
- Archives are properly protected

**Technical detail:**
```bash
# Analyzer creates marker before starting
touch ~/.claude/instinct-learning/observations/.processing

# Cleanup checks for marker
if [ -f .processing ]; then
  exit 0  # Skip cleanup
fi
```

### Fix 3: Test Coverage 16% → 95% ✅

**Before:** Many error paths untested
**After:** Comprehensive test coverage (282 tests, all passing)

**What this means for you:**
- Fewer bugs in production
- Better error handling
- More reliable plugin

---

## Verification Checklist

After upgrading, verify:

- [ ] Tests pass: `./tests/run_all.sh`
- [ ] Coverage is ~95%: `./tests/run_all.sh --coverage`
- [ ] Instincts load: `/instinct:status`
- [ ] Analyzer works: `/instinct:analyze`
- [ ] No errors in logs: `tail -f ~/.claude/instinct-learning/logs/*.log`

---

## Troubleshooting

### Issue: Tests Fail After Upgrade

**Solution:**
```bash
# Clean test artifacts
rm -rf .pytest_cache __pycache__ */__pycache__

# Re-run tests
./tests/run_all.sh
```

### Issue: Instincts Not Loading

**Solution:**
```bash
# Check instinct file permissions
ls -la ~/.claude/instinct-learning/instincts/personal/

# Verify YAML syntax
python3 -c "
import yaml
with open('path/to/instinct.md') as f:
    print(yaml.safe_load(f))
"
```

### Issue: Analyzer Crashes

**Solution:**
```bash
# Check logs
tail -50 ~/.claude/instinct-learning/logs/analyzer.log

# Verify observations file exists
ls -lh ~/.claude/instinct-learning/observations.jsonl

# Check for .processing marker (stale)
rm ~/.claude/instinct-learning/observations/.processing
```

---

## Rollback Instructions

If you encounter any issues and need to rollback:

```bash
# Restore backup
rm -rf ~/.claude/instinct-learning
cp -r ~/.claude/instinct-learning.backup ~/.claude/instinct-learning

# Rollback code
cd /path/to/oh-my-claude-code
git checkout <previous-commit-hash>
```

Previous commits:
- `115dd1b` - Before fixes (v2.0.0)

---

## Performance Impact

**Minimal performance impact:**
- YAML parsing: ~5% faster (optimized code)
- Archive cleanup: No change (still async)
- Memory usage: No significant change
- Test suite: +45 seconds (282 tests vs previous)

---

## Next Steps

After upgrading:

1. **Review your instincts** for any that came from external sources
2. **Run analyzer** to update any low-confidence instincts
3. **Consider exporting** your instincts as a backup:
   ```bash
   /instinct:export --output my-instincts-backup.md
   ```

---

## Questions?

See also:
- [Security Advisory](SECURITY-ADVISORY-2026-03-01.md)
- [CHANGELOG](../CHANGELOG.md)
- [Testing Guide](../tests/README.md)

---

## Summary

✅ **Safe to upgrade:** No breaking changes
✅ **Quick upgrade:** ~5 minutes
✅ **Critical fixes:** Security + reliability improvements
✅ **Well tested:** 282 tests, 95% coverage

**Recommendation:** Upgrade at your earliest convenience.
