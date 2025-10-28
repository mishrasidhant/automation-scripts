# ⚠️ DEPRECATED: Old Module Structure

**Status:** DEPRECATED as of v0.1.0  
**Date:** October 28, 2025  
**Migration Required:** Yes

---

## This Directory is Deprecated

The dictation module has been migrated to a modern UV-based package structure.

**Old location:** `modules/dictation/`  
**New location:** `src/automation_scripts/dictation/`

---

## What Changed?

### Package Management
- **Old:** pip + venv (`requirements/dictation.txt`)
- **New:** UV (`pyproject.toml` + `uv.lock`)

### Package Structure
- **Old:** `modules/dictation/dictate.py` (flat module)
- **New:** `src/automation_scripts/dictation/` (proper package)

### Configuration
- **Old:** `modules/dictation/config/dictation.env`
- **New:** `~/.config/automation-scripts/dictation.toml`

### Execution
- **Old:** `python modules/dictation/dictate.py --start`
- **New:** `uv run dictation-toggle --start`

---

## Migration Guide

See **[docs/MIGRATION-TO-UV.md](../../docs/MIGRATION-TO-UV.md)** for complete migration instructions.

### Quick Migration

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
cd /path/to/automation-scripts
uv sync --extra dictation

# 3. Update hotkey command
# Old: /path/to/modules/dictation/dictation-toggle.sh
# New: /path/to/scripts/dictation-toggle.sh

# 4. Test
uv run dictation-toggle --start
```

---

## Files in This Directory

These files are **kept for reference** during the migration period:

| File | Status | New Location |
|------|--------|--------------|
| `dictate.py` | DEPRECATED | `src/automation_scripts/dictation/dictate.py` |
| `dictation-toggle.sh` | DEPRECATED | `scripts/dictation-toggle.sh` |
| `config/dictation.env` | DEPRECATED | `~/.config/automation-scripts/dictation.toml` |
| `setup.sh` | DEPRECATED | Use `uv sync --extra dictation` |
| `test_dictate.py` | DEPRECATED | Needs update for new structure |

---

## Deprecation Timeline

- **v0.1.0 (Oct 2025):** Migration complete, old files marked deprecated
- **v0.2.0 (Est. Q1 2026):** Old files will be removed
- **Action Required:** Migrate before v0.2.0 release

---

## Need Help?

- **Migration Guide:** [docs/MIGRATION-TO-UV.md](../../docs/MIGRATION-TO-UV.md)
- **New Setup Guide:** [docs/ENVIRONMENT_SETUP.md](../../docs/ENVIRONMENT_SETUP.md)
- **README:** [README.md](../../README.md)

---

**⚡ The new UV-based system is 10-20x faster and more reliable!**

