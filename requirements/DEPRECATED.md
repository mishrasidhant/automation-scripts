# ⚠️ DEPRECATED: requirements/ Directory

**Status:** DEPRECATED as of v0.1.0  
**Date:** October 28, 2025

---

## This Directory is Deprecated

Dependencies are now managed by UV using `pyproject.toml` and `uv.lock`.

**Old system:** pip + requirements.txt files  
**New system:** UV + pyproject.toml

---

## Migration

Replace all pip commands with UV:

```bash
# OLD: pip install -r requirements/dictation.txt
# NEW: uv sync --extra dictation

# OLD: pip install -r requirements/all.txt
# NEW: uv sync --all-extras

# OLD: pip install -r requirements/dev.txt
# NEW: uv sync --group dev
```

---

## Files in This Directory

| File | Status | Replaced By |
|------|--------|-------------|
| `base.txt` | DEPRECATED | `pyproject.toml` [dependencies] |
| `dictation.txt` | DEPRECATED | `pyproject.toml` [project.optional-dependencies.dictation] |
| `dev.txt` | DEPRECATED | `pyproject.toml` [dependency-groups.dev] |
| `all.txt` | DEPRECATED | `uv sync --all-extras` |

---

## Why UV?

- **10-20x faster** installation
- **Locked dependencies** (reproducible builds)
- **Better dependency resolution**
- **No manual venv management**
- **Industry standard** (used by major Python projects)

---

See [docs/MIGRATION-TO-UV.md](../docs/MIGRATION-TO-UV.md) for complete migration guide.

