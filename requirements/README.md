# Requirements Directory

This directory contains Python dependency manifests for the systemd-automations project.

## Architecture

See: `docs/architecture/dependency-management.md` for complete architecture documentation.

---

## File Organization

| File | Purpose | Usage |
|------|---------|-------|
| `base.txt` | Shared dependencies across all modules | Minimal, truly universal packages only |
| `dictation.txt` | Voice dictation module dependencies | Audio, transcription, text injection |
| `backup.txt` | Backup automation dependencies (future) | Backup tools, cloud storage clients |
| `monitoring.txt` | System monitoring dependencies (future) | System stats, alerting |
| `dev.txt` | Development and testing tools | pytest, linters, debuggers |
| `all.txt` | Complete installation of all modules | Combines all module requirements |

---

## Installation

### Install Specific Module

```bash
# From project root
source scripts/setup-dev.sh dictation

# Or manually
source .venv/bin/activate
pip install -r requirements/dictation.txt
```

### Install All Modules

```bash
source scripts/setup-dev.sh all

# Or manually
source .venv/bin/activate
pip install -r requirements/all.txt
```

### Install Development Tools

```bash
source scripts/setup-dev.sh dev

# Or manually
source .venv/bin/activate
pip install -r requirements/dev.txt
```

---

## Guidelines

### Adding Dependencies

**Before adding a dependency, ask:**
1. Is this truly needed or nice-to-have?
2. Can functionality be achieved with stdlib?
3. Is this a lightweight, well-maintained package?
4. Does it have many transitive dependencies?

**If adding:**
1. Add to appropriate module file (e.g., `dictation.txt`)
2. Include comment explaining why it's needed
3. Use flexible version pinning: `package>=min.version`
4. Test installation in clean venv
5. Update module README documentation

### Version Pinning Strategy

**Use `>=` with major version:**
```txt
sounddevice>=0.4.6      # Requires at least 0.4.6, accepts 0.5.x, 0.6.x
numpy>=1.24.0           # Major version 1.x, at least 1.24
```

**Avoid exact pins unless absolutely necessary:**
```txt
# Bad (too restrictive)
sounddevice==0.4.6

# Good (flexible within reason)
sounddevice>=0.4.6,<0.6.0
```

**Exception:** Pin exact version if:
- Known breaking change in newer version
- Debugging specific version issue
- Reproducibility required for bug report

### Common Dependencies

**Base.txt:**
- Keep minimal
- Only truly shared utilities
- If in doubt, don't add it here

**Module-specific:**
- Clear ownership
- Document in comments
- Include `-r base.txt` at end

---

## File Structure

### Template for Module Requirements

```txt
# Module Name Requirements
# Description of module purpose

# Category: Main functionality
package-name>=1.0.0     # Why this package is needed
another-package>=2.3.0  # What it does

# Category: Optional/supporting
optional-package>=1.2.0  # When this is used

# Include base requirements
-r base.txt
```

### Example: dictation.txt

```txt
# Voice Dictation Module
# Audio recording, speech recognition, text injection

# Audio recording and manipulation
sounddevice>=0.4.6      # Python audio I/O
numpy>=1.24.0           # Audio data arrays

# Speech recognition
faster-whisper>=0.10.0  # Optimized Whisper transcription

# Include base requirements
-r base.txt
```

---

## Testing New Dependencies

```bash
# 1. Create test venv
python3 -m venv /tmp/test-venv
source /tmp/test-venv/bin/activate

# 2. Test installation
pip install package-name>=version

# 3. Verify imports
python -c "import package_name; print('OK')"

# 4. If successful, add to requirements file

# 5. Cleanup
deactivate
rm -rf /tmp/test-venv
```

---

## Updating Dependencies

### Check for Updates

```bash
source .venv/bin/activate
pip list --outdated
```

### Update Specific Package

```bash
source .venv/bin/activate
pip install --upgrade package-name

# Test modules still work
cd modules/dictation && python test_dictate.py
```

### Update All

```bash
source .venv/bin/activate
pip install --upgrade -r requirements/all.txt

# Full regression testing
pytest modules/
```

---

## Dependency Conflicts

**If two modules need conflicting versions:**

1. **Try to upgrade both** to newer compatible version
2. **Isolate one module** in separate venv (last resort)
3. **Refactor** to remove conflicting dependency
4. **Document** conflict and workaround

**Example conflict resolution:**
```txt
# Module A needs: package>=1.0,<2.0
# Module B needs: package>=2.0

# Solution: Upgrade module A to work with package 2.x
```

---

## System vs Python Dependencies

**Python packages go here (requirements/)**
- Pure Python libraries
- Python bindings to system libraries
- Installed via pip in venv

**System packages go elsewhere**
- C libraries (portaudio)
- Binary tools (xdotool)
- System services (libnotify)
- Documented in: `docs/architecture/SYSTEM_DEPS.md`

---

## Troubleshooting

### "No module named 'X'" Error

```bash
# Verify venv is activated
which python  # Should show .venv/bin/python

# If not activated
source .venv/bin/activate

# Install dependencies
pip install -r requirements/module-name.txt
```

### "Package 'X' requires 'Y'"

Some packages need system libraries:

```bash
# Check system dependencies
cat docs/architecture/SYSTEM_DEPS.md

# Install missing system package
sudo pacman -S package-name
```

### Corrupted Virtual Environment

```bash
# Remove venv
rm -rf .venv

# Recreate
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Reinstall all
pip install -r requirements/all.txt
```

---

## Best Practices

### DO:
- ✅ Comment why each dependency exists
- ✅ Group related packages together
- ✅ Use flexible version constraints
- ✅ Test in clean venv before committing
- ✅ Keep base.txt minimal
- ✅ Document breaking changes in comments

### DON'T:
- ❌ Add dependencies "just in case"
- ❌ Use exact version pins without reason
- ❌ Mix development and production deps
- ❌ Forget to include `-r base.txt`
- ❌ Add system packages here (use SYSTEM_DEPS.md)

---

## Related Documentation

- **Architecture:** `docs/architecture/dependency-management.md`
- **System Dependencies:** `docs/architecture/SYSTEM_DEPS.md`
- **Module README:** Each `modules/*/README.md` lists its requirements

---

## Questions?

1. **What's the difference between base.txt and all.txt?**
   - `base.txt` = minimal shared dependencies
   - `all.txt` = all module dependencies combined

2. **Should I install all.txt or specific modules?**
   - Development: Install what you're working on
   - Testing: Install all.txt
   - Production: Install only needed modules

3. **When should something go in base.txt?**
   - When 3+ modules all need it
   - When it's truly universal (logging, config parsing)
   - When in doubt: Keep it module-specific

4. **Can I have different Python versions?**
   - No, this architecture uses system Python
   - If needed, consider pyenv or per-module venvs

---

**Maintained by:** Project contributors  
**Last updated:** October 26, 2025

