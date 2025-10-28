# Epic: Dictation Module UV Migration & Reliable Startup - Brownfield Enhancement

## Epic Goal

Migrate the dictation module from pip/venv to UV package management and implement systemd-based keyboard shortcut persistence, transforming the installation from a complex 8-step manual process to a single-command modern Python application that reliably starts on boot.

## Epic Description

### Existing System Context

**Current Functionality:**
- Fully functional voice-to-text system using faster-whisper AI
- 1,044-line Python core script (`dictate.py`) with audio recording, transcription, and text injection
- 645-line bash setup script managing system dependencies, venv creation, and XFCE hotkey registration
- Multi-layered dependency management: pacman (system) → pip/venv (Python) → requirements.txt (module)
- XFCE keyboard shortcut registration via xfconf-query

**Technology Stack:**
- Python 3.11+ with venv + pip
- System dependencies: xdotool, libnotify, portaudio
- Python packages: sounddevice, numpy, faster-whisper
- XFCE4 keyboard shortcuts (xfconf-query, xfsettingsd)
- Bash configuration with .env files

**Integration Points:**
- X11 window system for keyboard injection (xdotool)
- XFCE settings daemon for hotkey monitoring
- System audio via portaudio/sounddevice
- Desktop notifications via libnotify
- Temporary filesystem (/tmp/dictation.lock)

**Critical Pain Points:**
1. **Hotkey Persistence Bug:** xfconf-query registers hotkey but xfsettingsd doesn't reload, causing hotkey to disappear after reboot
2. **No Dependency Locking:** pip installs can vary between machines (reproducibility issues)
3. **Complex Setup:** 645-line script with 8 manual steps, interactive prompts, no rollback
4. **Shared venv Conflicts:** Single `.venv/` for all modules causes potential version conflicts
5. **Incomplete Validation:** portaudio not checked during setup, only fails on Python import

### Enhancement Details

**What's Being Added/Changed:**

1. **UV Package Management:**
   - Replace `requirements/dictation.txt` with `pyproject.toml`
   - Implement UV workspace for monorepo support
   - Generate `uv.lock` for reproducible installations
   - Convert to src-layout package structure: `src/automation_scripts/dictation/`

2. **Systemd User Service:**
   - Create `~/.config/systemd/user/dictation-hotkey.service`
   - Service auto-starts on login, registers XFCE hotkey
   - Replaces fragile xfconf-query manual registration
   - Solves hotkey persistence issue permanently

3. **Modern Configuration:**
   - Replace `.env` files with TOML configuration
   - Implement XDG Base Directory specification:
     - Config: `~/.config/automation-scripts/dictation.toml`
     - Data: `~/.local/share/automation-scripts/dictation/`
     - Cache: `~/.cache/automation-scripts/dictation/`
   - Environment variable overrides for all settings
   - Backward compatibility NOT required (breaking changes acceptable)

4. **Simplified Installation:**
   - Target: `git clone → uv sync --extra dictation → systemctl --user enable`
   - System dependency validation with clear pre-flight checks
   - Single-command setup with comprehensive error messages

5. **Testing Infrastructure:**
   - pytest-based test suite (existing test_dictate.py enhanced)
   - CI-compatible test execution
   - Integration tests for systemd service registration

**How It Integrates:**

- **Python Core (`dictate.py`):** Minimal changes - update imports to package structure, replace config loading
- **System Dependencies:** Unchanged - still requires xdotool, libnotify, portaudio via pacman
- **XFCE Integration:** Enhanced - systemd service ensures hotkey registered on every boot
- **Audio Pipeline:** Unchanged - sounddevice → faster-whisper → xdotool flow remains identical
- **User Experience:** Improved - one-time setup, reliable operation, no manual daemon restarts

**Success Criteria:**

1. ✅ Keyboard shortcut persists across reboots without manual xfsettingsd restart
2. ✅ Fresh installation completes with: `uv sync --extra dictation && systemctl --user enable dictation-hotkey.service`
3. ✅ System dependency pre-flight checks catch portaudio, xdotool, libnotify before Python installation
4. ✅ Lock file (`uv.lock`) ensures identical dependency versions across all installations
5. ✅ Configuration migrated to `~/.config/automation-scripts/dictation.toml` with env var overrides
6. ✅ Test suite runs via `uv run pytest` with 100% pass rate for core functionality
7. ✅ Works on Manjaro/Arch Linux with XFCE/X11 (Wayland still unsupported, documented clearly)
8. ✅ Module can be imported as package: `from automation_scripts.dictation import DictationRecorder`

## Stories

### Story 1: UV Migration & Package Restructure

**Goal:** Convert dictation module from pip/venv to UV-managed package with proper Python project structure

**Key Deliverables:**
- Create `pyproject.toml` with project metadata, dependencies, and optional groups
- Implement UV workspace configuration at repository root
- Restructure code: `modules/dictation/dictate.py` → `src/automation_scripts/dictation/`
- Generate and validate `uv.lock` with all transitive dependencies
- Update `setup-dev.sh` to use UV commands instead of venv+pip
- Migrate requirements: `sounddevice>=0.4.6`, `numpy>=1.24.0`, `faster-whisper>=0.10.0`
- Define optional dependency groups: `[dictation]`, `[dev]`, `[test]`

**Acceptance Criteria:**
- `uv sync --extra dictation` installs all dependencies in <30 seconds
- `uv.lock` includes exact versions with hashes for security
- Package importable: `from automation_scripts.dictation import main`
- All existing functionality (recording, transcription, injection) works unchanged
- System dependency documentation updated with pre-installation requirements

---

### Story 2: Systemd Service & Hotkey Persistence

**Goal:** Implement systemd user service to reliably register XFCE keyboard shortcut on every boot

**Key Deliverables:**
- Create `dictation-hotkey.service` unit file template
- Implement service installation script: `install-hotkey-service.sh`
- Service functionality:
  - Runs on user login (`WantedBy=default.target`)
  - Executes xfconf-query to register `<Primary>apostrophe` → `dictation-toggle.sh`
  - Waits for xfsettingsd availability (use D-Bus activation)
  - Logs success/failure to journal
- Integrate service installation into main setup workflow
- Remove manual xfconf-query calls from `setup.sh`

**Service Design:**
```ini
[Unit]
Description=Dictation Keyboard Shortcut Registration
After=xfce4-session.target

[Service]
Type=oneshot
ExecStart=/home/%u/.local/bin/register-dictation-hotkey.sh
RemainAfterExit=yes

[Install]
WantedBy=default.target
```

**Acceptance Criteria:**
- Keyboard shortcut persists across system reboots (validated with 3 consecutive restarts)
- `systemctl --user status dictation-hotkey.service` shows active/success after login
- Service logs clearly indicate registration success or failure reasons
- Hotkey works immediately after first login without manual daemon restart
- Service handles xfsettingsd not ready gracefully (retries with timeout)

---

### Story 3: Configuration, Testing & Documentation

**Goal:** Modernize configuration system with TOML, implement comprehensive tests, and update all documentation

**Key Deliverables:**

**Configuration Modernization:**
- Create `dictation.toml` schema following XDG Base Directory spec
- Migrate 30+ settings from `dictation.env` to TOML sections:
  - `[whisper]` - model, device, compute_type, language, beam_size
  - `[audio]` - device, sample_rate, channels
  - `[text]` - paste_method, typing_delay, auto_capitalize
  - `[notifications]` - enable, tool, urgency, timeout
  - `[files]` - temp_dir, keep_temp_files, lock_file
- Implement config loader with precedence: CLI args > env vars > TOML > defaults
- Generate default config on first run
- Migration utility: `migrate-config.py` to convert old .env to TOML

**Testing:**
- Enhance `test_dictate.py` for pytest
- Add tests: config loading, audio device validation, mock transcription
- Create integration test suite: `test_integration.py`
  - Systemd service installation
  - Hotkey registration verification
  - End-to-end toggle workflow (mocked audio)
- CI workflow definition (GitHub Actions ready)

**Documentation:**
- Update `README.md` with UV installation instructions
- Create `docs/migration-guide.md` for existing users
- Update `ENVIRONMENT_SETUP.md` with UV commands
- Document new configuration system in `docs/configuration.md`
- Update system dependency requirements (emphasize portaudio)
- Add troubleshooting section for common UV/systemd issues

**Acceptance Criteria:**
- Configuration loads correctly with precedence: CLI > env > TOML > defaults
- Migration script successfully converts existing .env files to TOML
- Test suite runs via `uv run pytest` with 95%+ coverage on core functions
- Documentation clearly explains installation: `git clone` → `uv sync --extra dictation` → enable service
- Troubleshooting guide covers: missing system deps, systemd service failures, hotkey conflicts
- Breaking changes clearly documented with migration path

---

## Compatibility Requirements

**Breaking Changes Acceptable:**
- ⚠️ Configuration format changed from .env to TOML (migration script provided)
- ⚠️ Python package structure changed (import paths updated)
- ⚠️ Setup process simplified but incompatible with old workflow
- ⚠️ Minimum Python version: 3.11+ (was implicit 3.8+)

**Maintained Compatibility:**
- ✅ All CLI arguments to `dictate.py` unchanged (`--start`, `--stop`, `--toggle`)
- ✅ Lock file format (`/tmp/dictation.lock`) unchanged for graceful migration
- ✅ Audio file locations and formats unchanged
- ✅ XFCE keyboard shortcut behavior identical from user perspective
- ✅ xdotool text injection mechanism unchanged

**System Requirements:**
- OS: Manjaro/Arch Linux (primary), other Linux distributions (community supported)
- Desktop: XFCE4 (primary), other DEs may work but unsupported
- Display Server: X11 (required), Wayland explicitly not supported
- Python: 3.11 or newer
- System packages: python3, xdotool, libnotify, portaudio

---

## Risk Mitigation

### Primary Risk: Setup Script Complexity

**Risk:** Existing 645-line setup.sh has 8 major sections with interactive prompts, system package installation, and environment setup. UV migration could break the carefully orchestrated flow.

**Mitigation:**
- Keep setup.sh structure mostly intact, only replace Python env section (lines 188-244)
- Add comprehensive pre-flight system dependency checks before UV operations
- Implement dry-run mode: `./setup.sh --dry-run` to preview all changes
- Keep original setup.sh as `setup-legacy.sh` for 1-2 releases as fallback

### Secondary Risk: Systemd Service Conflicts

**Risk:** Users may have custom systemd units or XFCE startup scripts that conflict with new service.

**Mitigation:**
- Service uses unique name: `dictation-hotkey.service`
- Check for existing hotkey registration before overwriting
- Provide uninstall script: `systemctl --user disable dictation-hotkey.service`
- Log all registration attempts to systemd journal for debugging

### Tertiary Risk: Configuration Migration

**Risk:** Users have customized .env files with complex settings that could be lost or misinterpreted during TOML migration.

**Mitigation:**
- Migration script validates all env vars before conversion
- Backup original .env to `.env.backup.{timestamp}`
- Dry-run mode: `migrate-config.py --dry-run --show-diff`
- Support .env as fallback for 1 release cycle (deprecation warning)

---

## Rollback Plan

**If critical issues discovered post-migration:**

1. **Immediate Rollback (< 1 hour):**
   - Git revert to pre-UV commit
   - Users run: `git checkout v0.0.9-pre-uv && ./setup.sh`
   - Original requirements.txt and setup-legacy.sh available

2. **Partial Rollback (selective features):**
   - Keep UV package management (Story 1)
   - Rollback systemd service (Story 2): remove service, revert to xfconf-query
   - Rollback TOML config (Story 3): use .env fallback

3. **Recovery Procedure:**
   - Documented in `docs/ROLLBACK.md`
   - Test rollback procedure on clean VM before production migration
   - Maintain legacy branch for 2 releases: `legacy/venv-setup`

---

## Definition of Done

### Epic-Level Completion Criteria:

- ✅ **All 3 stories completed** with acceptance criteria met
- ✅ **Clean installation validated** on fresh Manjaro VM (no prior setup)
- ✅ **Upgrade path validated** from existing v0.0.9 installation
- ✅ **Hotkey persistence verified** across 3 consecutive reboots
- ✅ **Performance benchmarks met:**
  - Installation time: < 2 minutes (was 5-10 minutes)
  - First transcription: < 10 seconds (unchanged)
  - Hotkey registration: < 5 seconds on boot (new feature)
- ✅ **Documentation complete:**
  - README.md updated
  - Migration guide published
  - System requirements clearly documented
  - Troubleshooting guide with common issues
- ✅ **Testing validated:**
  - Unit tests: 95%+ coverage
  - Integration tests: all pass
  - Manual test procedures updated and executed
- ✅ **No regression in existing features:**
  - Audio recording quality unchanged
  - Transcription accuracy unchanged
  - Text injection behavior unchanged
  - Notification system unchanged
- ✅ **Breaking changes documented:**
  - Migration guide covers all breaking changes
  - Deprecation notices for removed features
  - Clear upgrade instructions

### Success Metrics (Post-Deployment):

- New user setup time: < 5 minutes (target)
- Hotkey persistence issue reports: 0 (from 100% of users affected)
- Installation failure rate: < 5% (from ~15% due to venv issues)
- Average installation time: < 2 minutes (from 5-10 minutes)

---

## Story Manager Handoff

**Story Manager Handoff:**

"Please develop detailed user stories for this brownfield epic. Key considerations:

- **Existing system:** Python 3.11+ monorepo with modules/dictation/ structure running on Manjaro/Arch Linux + XFCE + X11
- **Technology stack:** Python (sounddevice, numpy, faster-whisper), Bash, systemd, XFCE keyboard shortcuts
- **Integration points:**
  1. X11 window system via xdotool (text injection) - NO CHANGES to injection logic
  2. XFCE settings daemon (xfsettingsd) via xfconf-query - systemd service wraps existing registration
  3. System audio via portaudio - NO CHANGES to audio pipeline
  4. Desktop notifications via libnotify - NO CHANGES
  5. Temporary filesystem (/tmp/dictation.lock) - maintain JSON lock file format

- **Existing patterns to follow:**
  - Configuration loading: environment variables with fallback defaults
  - Error handling: user-friendly messages with actionable next steps
  - Setup script structure: clear sections with status messages (print_status function)
  - Testing approach: pytest with mock external dependencies (audio, xdotool)

- **Critical compatibility requirements:**
  - Lock file format (/tmp/dictation.lock) must remain JSON for graceful migration
  - CLI arguments (--start, --stop, --toggle) must not change
  - Audio recording behavior must be identical (sample rate, format, location)
  - Breaking changes to config format and package structure are ACCEPTABLE

- **Each story must include:**
  - Verification that existing audio recording/transcription functionality works after changes
  - System dependency validation (xdotool, libnotify, portaudio presence)
  - Clear installation testing steps on clean system
  - Rollback procedure if story introduces critical issues

The epic should maintain system integrity while delivering **reliable keyboard shortcut persistence** and **single-command modern Python installation** via UV package management. Users currently experience 100% failure rate for hotkey persistence across reboots - this is the #1 pain point to solve."

---

## Technical Notes

### UV Workspace Structure (Story 1)

```toml
# pyproject.toml (repository root)
[project]
name = "automation-scripts"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv.workspace]
members = ["src/automation_scripts/dictation"]

[project.optional-dependencies]
dictation = [
    "sounddevice>=0.4.6",
    "numpy>=1.24.0",
    "faster-whisper>=0.10.0"
]
dev = ["pytest>=7.4.0", "pytest-cov", "ruff", "mypy"]
```

### Systemd Service Architecture (Story 2)

**Service Install Location:** `~/.config/systemd/user/dictation-hotkey.service`

**Registration Script:** `~/.local/bin/register-dictation-hotkey.sh`
- Waits for xfsettingsd (max 30 seconds)
- Runs xfconf-query with absolute path to dictation-toggle.sh
- Logs to systemd journal: `journalctl --user -u dictation-hotkey.service`

**Enable Commands:**
```bash
systemctl --user enable dictation-hotkey.service
systemctl --user start dictation-hotkey.service
```

### Configuration Schema (Story 3)

**File:** `~/.config/automation-scripts/dictation.toml`

```toml
[whisper]
model = "base.en"
device = "cpu"
compute_type = "int8"
language = "en"
beam_size = 5
temperature = 0.0

[audio]
device = "default"
sample_rate = 16000
channels = 1

[text]
paste_method = "xdotool"
typing_delay = 12
auto_capitalize = false
strip_spaces = true

[notifications]
enable = true
tool = "notify-send"
urgency = "normal"
timeout = 3000

[files]
temp_dir = "/tmp/dictation"
keep_temp_files = false
lock_file = "/tmp/dictation.lock"
```

**Environment variable overrides:**
- `DICTATION_WHISPER_MODEL` overrides `[whisper].model`
- `DICTATION_AUDIO_DEVICE` overrides `[audio].device`
- etc.

---

## Related Documents

- **Current State Analysis:** `docs/current-state.md` (1,249 lines - comprehensive brownfield documentation)
- **Original Setup Script:** `modules/dictation/setup.sh` (645 lines)
- **Core Python Script:** `modules/dictation/dictate.py` (1,044 lines)
- **Configuration Template:** `modules/dictation/config/dictation.env` (137 lines)
- **Testing Procedures:** `modules/dictation/MANUAL_TESTING.md`

---

## Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-27 | 1.0 | Initial epic creation for UV migration with systemd hotkey persistence | John (Product Manager) |

---

**Epic Status:** READY FOR STORY DEVELOPMENT  
**Estimated Complexity:** 3 stories, ~2-3 weeks development  
**Priority:** HIGH (resolves #1 user pain point: hotkey persistence)  
**Target Release:** v0.1.0 (UV Migration Release)

