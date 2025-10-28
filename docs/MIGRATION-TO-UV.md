# Migration Guide: UV Package Management

**Version:** 0.1.0  
**Date:** October 28, 2025  
**Status:** Production Ready

This guide helps existing users migrate from the old pip/venv setup to the new UV-based package management system.

---

## 📋 What Changed?

### Breaking Changes

1. **Package Management:** `pip` + `venv` → `uv` (faster, locked dependencies)
2. **Package Structure:** Flat module → `src/` layout (proper Python package)
3. **Configuration:** `.env` files → `.toml` files (XDG-compliant)
4. **Import Paths:** Direct script execution → Package imports
5. **Python Requirement:** 3.10+ → 3.11+ (required for tomllib)

### What Stayed the Same

✅ **Runtime behavior unchanged:**
- CLI arguments (`--start`, `--stop`, `--toggle`)
- Lock file location (`/tmp/dictation.lock`)
- Audio recording quality (16kHz, mono, WAV)
- Text injection mechanism (xdotool)
- Desktop notifications (libnotify)
- Hotkey integration (still works with XFCE)

---

## 🚀 Quick Migration Path

### Step 1: Install UV

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart shell or run:
source $HOME/.local/bin/env

# Verify installation
uv --version
```

### Step 2: Update Repository

```bash
cd /path/to/automation-scripts

# Pull latest changes
git pull origin main

# Verify UV migration files exist
ls pyproject.toml uv.lock src/automation_scripts/
```

### Step 3: Backup Old Configuration (Optional)

```bash
# Backup your old .env config (if customized)
cp modules/dictation/config/dictation.env ~/dictation.env.backup
```

### Step 4: Install Dependencies with UV

```bash
# Remove old venv (no longer needed)
rm -rf .venv

# Install with UV (takes < 30 seconds)
uv sync --extra dictation

# Verify installation
uv run dictation-toggle --help
```

### Step 5: Migrate Configuration

If you customized `modules/dictation/config/dictation.env`, convert it to TOML:

```bash
# Create config directory
mkdir -p ~/.config/automation-scripts

# Copy example config
cp config/dictation.toml.example ~/.config/automation-scripts/dictation.toml

# Edit with your settings (see mapping below)
vim ~/.config/automation-scripts/dictation.toml
```

**Configuration Mapping:**

| Old (.env) | New (.toml) | Section |
|------------|-------------|---------|
| `DICTATION_WHISPER_MODEL=base.en` | `model = "base.en"` | `[whisper]` |
| `DICTATION_WHISPER_DEVICE=cpu` | `device = "cpu"` | `[whisper]` |
| `DICTATION_AUDIO_DEVICE=default` | `device = "default"` | `[audio]` |
| `DICTATION_TYPING_DELAY=12` | `typing_delay = 12` | `[text]` |
| `DICTATION_PASTE_METHOD=xdotool` | `paste_method = "xdotool"` | `[text]` |
| `DICTATION_ENABLE_NOTIFICATIONS=true` | `enable = true` | `[notifications]` |

**Example TOML:**

```toml
[whisper]
model = "base.en"
device = "cpu"
compute_type = "int8"

[audio]
device = "default"

[text]
paste_method = "xdotool"
typing_delay = 12
```

### Step 6: Update Hotkey Command (XFCE)

If you have a hotkey configured, update the command path:

**Old:**
```
/path/to/modules/dictation/dictation-toggle.sh
```

**New:**
```
/path/to/scripts/dictation-toggle.sh
```

**To update:**
1. Open Settings → Keyboard → Application Shortcuts
2. Find your `Ctrl+'` (or configured) shortcut
3. Edit command to new path: `/path/to/scripts/dictation-toggle.sh`
4. Test with hotkey

### Step 7: Test Everything

```bash
# Test from command line
uv run dictation-toggle --start
# Speak something...
uv run dictation-toggle --stop
# Text should appear!

# Test with hotkey
# Press Ctrl+' (or your configured key)
```

---

## 🔍 Troubleshooting

### Problem: UV command not found

**Solution:**
```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Problem: Configuration not loading

**Check configuration priority:**
```bash
# Show current config
uv run python -m automation_scripts.dictation.config

# Verify TOML file location
ls -la ~/.config/automation-scripts/dictation.toml
```

**Priority (highest to lowest):**
1. Environment variables (`DICTATION_*`)
2. TOML file (`~/.config/automation-scripts/dictation.toml`)
3. Built-in defaults

### Problem: Old venv still being used

**Solution:**
```bash
# Remove old venv completely
rm -rf .venv

# Reinstall with UV
uv sync --extra dictation

# Verify UV is managing packages
which python  # Should show system Python, not .venv
uv run which python  # Should show UV's managed Python
```

### Problem: Hotkey stopped working

**Check:**
```bash
# Test script directly
/path/to/scripts/dictation-toggle.sh

# Check UV in PATH
which uv

# Check pyproject.toml exists
ls -l pyproject.toml
```

**Fix:**
- Update hotkey command to new script location
- Ensure UV is in PATH (add to `~/.bashrc`)
- Script must be executable: `chmod +x scripts/dictation-toggle.sh`

### Problem: Missing dependencies error

**Solution:**
```bash
# Check system dependencies
sudo pacman -Q portaudio xdotool libnotify

# Install if missing
sudo pacman -S portaudio xdotool libnotify

# Reinstall Python packages
uv sync --extra dictation --reinstall
```

### Problem: Import errors

**This usually means:**
- Running from wrong directory (must be in project root)
- pyproject.toml missing
- Package not installed

**Solution:**
```bash
cd /path/to/automation-scripts  # Important!
uv sync --extra dictation
uv run dictation-toggle --help  # Should work
```

---

## 🔧 Hotkey Persistence (Systemd Service)

**New in UV Migration:** Systemd user service for automatic hotkey registration on login.

### The Problem

After rebooting, the XFCE keyboard shortcut (Ctrl+') often stops working because `xfsettingsd` (XFCE Settings Daemon) doesn't reload the configuration automatically. This affects 100% of users who manually configure the hotkey.

### The Solution

A systemd user service that:
- Runs automatically on every login
- Waits for xfsettingsd to be available
- Registers the hotkey via xfconf-query
- Sends a graceful reload signal to xfsettingsd
- Ensures hotkey works immediately after boot

### Installation

**One-command setup:**
```bash
cd /path/to/automation-scripts
./scripts/install-hotkey-service.sh
```

This will:
1. Install systemd service file to `~/.config/systemd/user/dictation-hotkey.service`
2. Install registration/unregistration scripts to `~/.local/bin/`
3. Enable service (starts on login)
4. Start service immediately
5. Verify installation

### Verification

```bash
# Check service status
systemctl --user status dictation-hotkey.service

# Run comprehensive diagnostic
./scripts/check-hotkey-status.sh

# View logs
journalctl --user -u dictation-hotkey.service
```

### Troubleshooting Hotkey Persistence

**Issue: Hotkey doesn't work after reboot**

```bash
# Restart the service
systemctl --user restart dictation-hotkey.service

# Check if service is enabled
systemctl --user is-enabled dictation-hotkey.service

# Enable if not
systemctl --user enable dictation-hotkey.service
```

**Issue: Service fails to start**

```bash
# Check logs for errors
journalctl --user -u dictation-hotkey.service -n 50

# Common causes:
# - xfsettingsd not running (not XFCE environment)
# - Scripts not executable
# - Project moved (paths changed)

# Manual registration (bypass service)
./scripts/register-hotkey.sh
```

**Issue: Service installed but hotkey still not persistent**

```bash
# Verify xfconf registration
xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe"

# Should output: /path/to/automation-scripts/scripts/dictation-toggle.sh

# Check if xfsettingsd is running
pgrep xfsettingsd

# Reload xfsettingsd manually
pkill -HUP xfsettingsd
```

### Uninstallation

```bash
# Unregister hotkey
./scripts/unregister-hotkey.sh

# Disable and stop service
systemctl --user disable --now dictation-hotkey.service

# Remove files (optional)
rm ~/.config/systemd/user/dictation-hotkey.service
rm ~/.local/bin/{register,unregister}-hotkey.sh
systemctl --user daemon-reload
```

### Manual Alternative (Not Recommended)

If you prefer not to use the systemd service:

1. Open XFCE Settings → Keyboard → Application Shortcuts
2. Add shortcut: `/path/to/automation-scripts/scripts/dictation-toggle.sh`
3. Key: Ctrl+'
4. **Note:** You'll need to manually re-register after each reboot or run `./scripts/register-hotkey.sh`

### Technical Details

For developers and advanced users:

**Service Architecture:**
- **Type:** oneshot (runs once per login)
- **Target:** After=graphical-session.target (waits for GUI)
- **Restart:** no (manual restart only)
- **Logs:** journalctl --user -u dictation-hotkey.service

**Key Scripts:**
- `register-hotkey.sh` - Registration logic with 30s timeout for xfsettingsd
- `unregister-hotkey.sh` - Cleanup and removal
- `install-hotkey-service.sh` - Installation and verification
- `check-hotkey-status.sh` - Comprehensive diagnostic tool

**For more details:** See `docs/stories/story-9-systemd-hotkey.md`

---

## 🔄 Rollback Plan

If you encounter critical issues and need to rollback:

### Option 1: Use Old Setup (Temporary)

```bash
# Old files are still present in modules/dictation/
cd modules/dictation

# Use old setup script
./setup.sh

# Use old activation
source ../../.venv/bin/activate
python dictate.py --start
```

### Option 2: Git Revert

```bash
# Revert to pre-UV version
git log --oneline  # Find commit before UV migration
git checkout <commit-hash>

# Reinstall old way
source scripts/setup-dev.sh dictation
```

### Option 3: Report Issue

If you find bugs:
1. Check [GitHub Issues](https://github.com/mishrasidhant/automation-scripts/issues)
2. Create new issue with:
   - Error message
   - Steps to reproduce
   - System info: `uv --version`, `python --version`, `uname -a`

---

## 📊 Benefits of UV Migration

### Speed Improvements

| Operation | Old (pip) | New (UV) | Improvement |
|-----------|-----------|----------|-------------|
| Clean install | 5-10 min | < 30 sec | **10-20x faster** |
| Reinstall (cached) | 2-3 min | < 5 sec | **24-36x faster** |
| Lock file generation | N/A | < 1 sec | New feature |

### Reproducibility

**Old:**
- Different versions installed on different machines
- No guarantee of working dependencies
- Manual venv management

**New:**
- Exact versions locked in `uv.lock`
- Verified dependency graph with hashes
- Automatic venv management

### Developer Experience

**Old:**
```bash
cd automation-scripts
source .venv/bin/activate  # Must remember
pip install -r requirements/dictation.txt  # Slow
python modules/dictation/dictate.py --start  # Long path
deactivate  # Must remember
```

**New:**
```bash
cd automation-scripts
uv sync --extra dictation  # Fast
uv run dictation-toggle --start  # Short, works anywhere
# No activation/deactivation needed!
```

---

## 🎯 New Features

### XDG Base Directory Compliance

Configuration now follows Linux standards:

- **Config:** `~/.config/automation-scripts/dictation.toml`
- **Data:** `~/.local/share/automation-scripts/dictation/`
- **Cache:** `~/.cache/automation-scripts/dictation/`

### Proper Python Package

Can now import as a package:

```python
from automation_scripts.dictation import main
main()
```

### Entry Point

```bash
# Works from anywhere (no path needed)
uv run dictation-toggle --start
```

### Development Tools

```bash
# Install dev tools
uv sync --group dev --extra dictation

# Linting and formatting
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run mypy src/

# Testing with coverage
uv run pytest --cov
```

---

## 📚 Additional Resources

- **Example Config:** `config/dictation.toml.example`
- **Architecture Docs:** `docs/architecture/dependency-management.md`
- **Story Document:** `docs/stories/story-8-uv-migration.md`
- **UV Documentation:** https://github.com/astral-sh/uv

---

## ✅ Migration Checklist

Print this out or check off as you go:

- [ ] Install UV package manager
- [ ] Pull latest code from repository
- [ ] Backup old .env configuration (if customized)
- [ ] Remove old .venv directory
- [ ] Run `uv sync --extra dictation`
- [ ] Migrate configuration to TOML format
- [ ] **Install systemd service for hotkey persistence** (recommended)
  - [ ] Run `./scripts/install-hotkey-service.sh`
  - [ ] Verify: `systemctl --user status dictation-hotkey.service`
  - [ ] Run diagnostic: `./scripts/check-hotkey-status.sh`
- [ ] Test command line execution
- [ ] Test hotkey integration (press Ctrl+')
- [ ] Verify transcription works
- [ ] Verify text injection works
- [ ] Verify notifications work
- [ ] **Test reboot persistence** (press Ctrl+' after reboot)
- [ ] Remove backup files once confirmed working

---

**Questions or Issues?**

- Check troubleshooting section above
- Review `docs/ENVIRONMENT_SETUP.md`
- Open an issue on GitHub

**Happy dictating! 🎤**

