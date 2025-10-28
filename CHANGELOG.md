# Changelog

All notable changes to the automation-scripts dictation module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-10-28 - Post-UV Migration Cleanup

### 🧹 Cleanup

**Removed Deprecated Directories:**
- `modules/dictation/` - Old flat module structure (replaced by src/automation_scripts/dictation/)
- `requirements/` - Old pip requirements (replaced by pyproject.toml + uv.lock)
- `staging/` - Unused playground scripts
- `htmlcov/` - Generated HTML coverage reports (not needed in repo)

**Removed Outdated Documentation:**
- `docs/ARCHITECTURE_SUMMARY.md` - Superseded by ARCHITECTURE.md
- `docs/DICTATION_ARCHITECTURE.md` - Duplicate architecture documentation
- `docs/current-state.md` - Temporary migration tracking file
- `docs/SETUP_CHECKLIST.md` - Old pip-based setup (superseded by README.md)
- `docs/CONFIGURATION_OPTIONS.md` - Old .env format (superseded by USER-GUIDE.md)
- `docs/ENVIRONMENT_SETUP.md` - Manual venv setup (UV auto-manages)
- `docs/SYSTEM_PROFILE.md` - Machine-specific, not general documentation
- `docs/USER_PREFERENCES.md` - Redundant with USER-GUIDE.md

### 📚 Documentation

**Added:**
- `docs/index.md` - Complete documentation index and navigation
- `docs/stories/README.md` - Story documentation index with archive markers
- `docs/qa/gates/README.md` - QA gate index with archive markers

**Updated:**
- All documentation now references UV-based workflows exclusively
- Stories 1-7 clearly marked as "Archived (Pre-UV Era)"
- QA gates DICT-001 through DICT-007 marked as archived

### ✅ Validation

**Test Results:**
- Test suite: 58/58 tests passing (current UV-based tests)
- Previous: 112 tests (included 54 deprecated tests in modules/dictation/)
- Coverage: 31% (baseline maintained)
- No breaking changes to active codebase
- All imports working correctly
- CLI commands operational
- pyproject.toml updated: removed obsolete "modules" testpath

**Story:** DICT-012 (Post-UV Cleanup)  
**QA Gate:** PASS ✅

## [0.1.0] - 2025-10-28

### Added

#### Story 8: UV Package Management
- **UV-based dependency management** for faster, more reliable installation
- **Proper Python package structure** with `src/` layout
- **TOML configuration system** replacing `.env` files
- **XDG Base Directory compliance** for config, data, and cache
- **Environment variable overrides** for all configuration options
- **Configuration validation** with helpful error messages
- **Locked dependencies** via `uv.lock` for reproducible builds
- **Entry point** for package: `uv run dictation-toggle`

#### Story 9: Systemd Service Integration
- **Systemd user service** for automatic hotkey registration on login
- **Hotkey persistence across reboots** - no more manual re-registration
- **One-command installation** via `install-hotkey-service.sh`
- **Service management scripts**: `register-hotkey.sh`, `unregister-hotkey.sh`
- **Proper service lifecycle** with RemainAfterExit and SIGHUP reload

#### Story 10: Signal Handling Fix
- **Fixed critical SIGTERM hang** that blocked recording indefinitely
- **Graceful cleanup** on signal reception
- **Flag-based signal handling** for safe, non-blocking shutdown
- **Resource cleanup** ensures lock files and temp files are properly removed

#### Story 10.5: Startup Reliability
- **Auto-sync UV environment** on first run after boot
- **Automatic dependency detection** and sync when needed
- **Better error messages** when environment setup required
- **Improved logging** for troubleshooting first-run issues
- **Zero-touch operation** after system updates

#### Story 10.6: Enhanced Diagnostics
- **Comprehensive diagnostic tool**: `check-hotkey-status.sh`
- **Multi-layer health checks**: systemd, hotkeys, UV environment, recent logs
- **Clear status indicators** with ✓/✗ symbols
- **Recent operation logs** display for quick troubleshooting
- **Actionable error messages** to guide problem resolution

#### Story 11: Testing, Configuration & Documentation
- **Complete test suite** with 58 passing tests
- **Pytest integration** with fixtures and mocking
- **Configuration tests** (29 tests, 75% coverage)
- **Constants tests** (29 tests, 96% coverage)
- **Test documentation** in `tests/README.md`
- **Configuration examples**:
  - `config/dictation-minimal.toml` - Bare minimum setup
  - `config/dictation-performance.toml` - Speed-optimized
  - `config/dictation-accuracy.toml` - Quality-optimized
- **Comprehensive documentation**:
  - `docs/ARCHITECTURE.md` - Technical design and component architecture
  - `docs/USER-GUIDE.md` - Tips, best practices, and usage guide
  - `docs/TROUBLESHOOTING.md` - Problem-solving guide with solutions
  - `docs/DEVELOPMENT.md` - Developer and contributor guide
  - Updated `docs/MIGRATION-TO-UV.md` - Includes Stories 9-11 changes
  - `CHANGELOG.md` - This file!
  - Enhanced `README.md` - Reflects all recent improvements

### Changed

#### Story 8: UV Package Management
- **Migrated from pip/venv to UV** (10-100x faster dependency resolution)
- **Configuration format** from `.env` to `.toml` (more expressive, validation)
- **Package structure** from flat to `src/` layout (proper Python packaging)
- **Import paths** now use package: `from automation_scripts.dictation import ...`
- **Python requirement** raised to 3.11+ (for tomllib stdlib)
- **Configuration location** moved to `~/.config/automation-scripts/` (XDG compliant)

#### Story 10: Signal Handling Fix
- **Recording stop behavior** now instantaneous (was: could hang indefinitely)
- **Signal handler** redesigned to use flags instead of blocking operations

#### Story 11: Testing, Configuration & Documentation
- **README.md** completely rewritten with modern structure and all features
- **Configuration validation** improved with clearer error messages
- **Example configuration** expanded with comprehensive comments

### Fixed

#### Story 10: Signal Handling Fix
- **Critical bug**: SIGTERM would cause recording to hang indefinitely
- **Lock files** now properly cleaned up on abnormal termination
- **Zombie processes** eliminated through proper signal handling
- **Resource leaks** fixed by ensuring cleanup in all exit paths

#### Story 10.5: Startup Reliability
- **"Module not found"** errors on first run after boot
- **Import errors** when dependencies out of sync
- **Silent failures** now have clear error messages

#### Story 10.6: Enhanced Diagnostics
- **Obscure error messages** replaced with clear diagnostics
- **Difficult troubleshooting** made easier with status script
- **Hidden issues** now visible in comprehensive health checks

### Deprecated

None in this release.

### Removed

#### Story 8: UV Package Management
- **Old venv-based installation** (replaced by UV)
- **pip requirements files** (replaced by pyproject.toml and uv.lock)
- **Environment file configuration** (replaced by TOML)
- **modules/dictation/** directory (moved to `src/automation_scripts/dictation/`)

### Security

- **Local-only processing** maintained - no cloud services, no data transmission
- **XDG directory permissions** enforced (config dir: 0o700)
- **No plaintext secrets** in configuration (not applicable, but noted)

## [0.0.1] - 2025-10-27 (Pre-UV Migration)

### Features (Historical)

- Voice dictation with Whisper AI models
- Hotkey integration via XFCE keyboard shortcuts
- Audio recording with sounddevice
- Text injection via xdotool
- Desktop notifications
- Lock file state management
- Basic .env configuration
- 54 existing unit tests in test_dictate.py

### Known Issues (Resolved in 0.1.0)

- ❌ Manual hotkey registration required after reboot → Fixed in Story 9
- ❌ SIGTERM hang during recording → Fixed in Story 10
- ❌ Manual UV sync needed after boot → Fixed in Story 10.5
- ❌ Difficult troubleshooting → Fixed in Story 10.6
- ❌ No test coverage for new modules → Fixed in Story 11
- ❌ Limited documentation → Fixed in Story 11

---

## Version History Summary

| Version | Date | Description |
|---------|------|-------------|
| **0.1.0** | 2025-10-28 | **UV Migration Release** - Complete modernization with UV, systemd, testing, and comprehensive docs |
| 0.0.1 | 2025-10-27 | Pre-UV baseline - working but with known issues |

---

## Upgrade Instructions

### From 0.0.1 to 0.1.0

**This is a major update with significant improvements. Highly recommended!**

**Quick upgrade**:
```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 2. Pull latest code
cd /path/to/automation-scripts
git pull

# 3. Install with UV
rm -rf .venv  # Remove old venv
uv sync --extra dictation

# 4. Migrate configuration
mkdir -p ~/.config/automation-scripts
cp config/dictation.toml.example ~/.config/automation-scripts/dictation.toml
# Edit dictation.toml with your settings

# 5. Install systemd service (new!)
./scripts/install-hotkey-service.sh

# 6. Verify installation
./scripts/check-hotkey-status.sh

# 7. Test
uv run dictation-toggle --start
# Speak something
uv run dictation-toggle --stop
```

**Detailed migration guide**: See [docs/MIGRATION-TO-UV.md](docs/MIGRATION-TO-UV.md)

**Breaking changes**: None! All changes are backward compatible at the runtime level. Configuration format changed (`.env` → `.toml`), but old behavior preserved.

---

## Contributing

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for development guidelines.

---

## Links

- **Repository**: https://github.com/mishrasidhant/automation-scripts
- **Issues**: https://github.com/mishrasidhant/automation-scripts/issues
- **Documentation**: [docs/](docs/)
- **User Guide**: [docs/USER-GUIDE.md](docs/USER-GUIDE.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

**Maintained by**: Sidhant Dixit  
**License**: MIT

