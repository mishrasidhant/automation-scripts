# Story 9: Systemd Service & Hotkey Persistence

<!-- Source: Epic UV Migration (Story 2 of 3) -->
<!-- Context: Brownfield enhancement to existing dictation module -->

**Story ID:** DICT-009  
**Epic:** UV Migration & Reliable Startup - Brownfield Enhancement  
**Priority:** HIGH (Resolves #1 user pain point: 100% hotkey persistence failure)  
**Complexity:** Medium  
**Estimated Effort:** 4-6 hours  
**Depends On:** Story 8 (UV Migration & Package Restructure) - ✅ COMPLETE  
**Blocks:** Story 10 (Advanced Testing & Documentation)

---

## Status: Draft

---

## Story

**As a** user,  
**I want** the keyboard shortcut (Ctrl+') to persist across reboots automatically,  
**so that** I don't have to manually reconfigure or restart xfsettingsd after every startup.

---

## Context Source

- **Source Document:** `docs/epics/epic-uv-migration.md` (Story 2)
- **Enhancement Type:** Systemd Service Integration (Hotkey Persistence Fix)
- **Existing System Impact:** Solves critical bug where xfconf-query registers hotkey but xfsettingsd doesn't reload, causing hotkey loss on reboot
- **Current State Analysis:** `docs/current-state.md` (Lines 557-585) - 100% of users affected by hotkey persistence issue

---

## Problem Statement

**Current Pain Point (100% Failure Rate):**

Users experience keyboard shortcut persistence failure across reboots. The hotkey registration process uses `xfconf-query` which successfully writes to XFCE configuration XML, but the `xfsettingsd` daemon doesn't reload the new configuration. After reboot, the hotkey is "forgotten" and users must manually restart the daemon or re-register via GUI.

**Root Cause:**
1. `xfconf-query` writes to `~/.config/xfce4/xfconf/xfce4-keyboard-shortcuts/xfce4-keyboard-shortcuts.xml`
2. XML file persists correctly
3. BUT: `xfsettingsd` (XFCE Settings Daemon) doesn't reload configuration
4. On reboot, daemon loads stale configuration state
5. Manually killing/restarting xfsettingsd is risky (affects user session)

**Current Workaround (Manual):**
```bash
pkill xfsettingsd
xfsettingsd &
```

**Target Solution:**

Create a systemd user service that runs on login, waits for xfsettingsd availability, registers the hotkey via xfconf-query, and forces a reload via `pkill -HUP xfsettingsd` (graceful reload signal). This ensures the hotkey is registered and active immediately after every boot.

---

## Acceptance Criteria

### Functional Requirements

1. **Systemd Service Created and Functional**
   - Service file created: `systemd/dictation-hotkey.service`
   - Service installs to: `~/.config/systemd/user/dictation-hotkey.service`
   - Service type: `oneshot` (runs once per login)
   - Dependency: `After=graphical-session.target` (ensures GUI session ready)
   - `RemainAfterExit=yes` (maintains "active" state after completion)

2. **Registration Script Created**
   - Script: `scripts/register-hotkey.sh`
   - Installs to: `~/.local/bin/register-hotkey.sh`
   - Functionality:
     - Waits for xfsettingsd availability (max 30 seconds timeout)
     - Runs xfconf-query to register `<Primary>apostrophe` → `{project_root}/scripts/dictation-toggle.sh`
     - Sends `SIGHUP` to xfsettingsd (graceful reload: `pkill -HUP xfsettingsd`)
     - Verifies registration success via xfconf-query readback
     - Logs all operations to systemd journal

3. **Unregistration Script Created**
   - Script: `scripts/unregister-hotkey.sh`
   - Functionality:
     - Removes xfconf-query registration
     - Reloads xfsettingsd
     - Cleans up gracefully

4. **Installation Helper Script Created**
   - Script: `scripts/install-hotkey-service.sh`
   - Functionality:
     - Copies service file to `~/.config/systemd/user/`
     - Copies registration/unregistration scripts to `~/.local/bin/`
     - Sets executable permissions
     - Runs `systemctl --user daemon-reload`
     - Enables service: `systemctl --user enable dictation-hotkey.service`
     - Starts service immediately: `systemctl --user start dictation-hotkey.service`
     - Verifies service status

5. **Diagnostic Script Created**
   - Script: `scripts/check-hotkey-status.sh`
   - Functionality:
     - Checks systemd service status
     - Verifies xfconf-query registration
     - Tests if xfsettingsd is running
     - Shows journalctl logs for service
     - Provides troubleshooting tips

6. **Hotkey Persistence Verified**
   - Keyboard shortcut (Ctrl+') works immediately after login
   - Hotkey persists across 3 consecutive reboots (validated)
   - `systemctl --user status dictation-hotkey.service` shows `active (exited)` status
   - No manual xfsettingsd restart required

### Integration Requirements

7. **Existing Functionality Preserved**
   - Audio recording pipeline unchanged
   - Transcription accuracy unchanged
   - Text injection mechanism unchanged
   - Lock file behavior unchanged
   - Notifications unchanged
   - `dictation-toggle.sh` works before and after service installation

8. **Service Logging and Diagnostics**
   - Logs visible via: `journalctl --user -u dictation-hotkey.service`
   - Log messages include:
     - Startup timestamp
     - xfsettingsd wait status
     - xfconf-query command result
     - Reload signal sent confirmation
     - Verification result
     - Any errors with actionable messages

9. **Graceful Failure Handling**
   - If xfsettingsd not available after 30s timeout: Log error, exit cleanly
   - If xfconf-query fails: Log error with troubleshooting steps
   - If not running XFCE: Detect and exit gracefully with message
   - Service failure doesn't block user login
   - Manual fallback instructions in logs

### Quality Requirements

10. **Documentation Complete**
    - Service design documented in story
    - Installation instructions in README.md
    - Troubleshooting section for service issues
    - Uninstallation procedure documented
    - Manual verification steps provided

---

## Acceptance Testing

### Test 1: Clean Installation and Service Activation

**Preconditions:** Story 8 (UV Migration) complete, fresh user session

**Steps:**
1. Run installation script: `./scripts/install-hotkey-service.sh`
2. Verify service copied: `ls ~/.config/systemd/user/dictation-hotkey.service`
3. Verify scripts copied: `ls ~/.local/bin/{register,unregister}-hotkey.sh`
4. Check service enabled: `systemctl --user is-enabled dictation-hotkey.service`
5. Check service status: `systemctl --user status dictation-hotkey.service`
6. Check logs: `journalctl --user -u dictation-hotkey.service --no-pager`
7. Test hotkey: Press Ctrl+' and verify dictation starts
8. Verify xfconf registration: `xfconf-query -c xfce4-keyboard-shortcuts -l | grep apostrophe`

**Expected Results:**
- ✓ Installation completes without errors
- ✓ Service status shows `active (exited)` (oneshot with RemainAfterExit=yes)
- ✓ Logs show successful registration and reload
- ✓ Hotkey responds immediately (Ctrl+')
- ✓ xfconf-query shows registered hotkey path

---

### Test 2: Reboot Persistence (Critical)

**Preconditions:** Test 1 completed successfully

**Steps:**
1. Reboot system: `sudo reboot`
2. Login to XFCE session
3. Wait 10 seconds for services to stabilize
4. Check service status: `systemctl --user status dictation-hotkey.service`
5. Test hotkey: Press Ctrl+' immediately
6. Verify dictation starts without manual intervention
7. Repeat reboot 2 more times (total 3 reboots)

**Expected Results:**
- ✓ Service starts automatically on each login
- ✓ Hotkey works immediately after each reboot (within 5 seconds of login)
- ✓ No manual xfsettingsd restart needed
- ✓ Service logs show successful registration on each boot

---

### Test 3: Service Failure Handling

**Preconditions:** Service installed

**Steps:**
1. Stop xfsettingsd: `pkill xfsettingsd` (don't restart)
2. Restart service: `systemctl --user restart dictation-hotkey.service`
3. Check service status: `systemctl --user status dictation-hotkey.service`
4. Check logs: `journalctl --user -u dictation-hotkey.service -n 20`
5. Verify error messages are clear and actionable
6. Restart xfsettingsd: `xfsettingsd &`
7. Restart service again
8. Verify success this time

**Expected Results:**
- ✓ Service handles missing xfsettingsd gracefully (timeout message)
- ✓ Error logs include troubleshooting steps
- ✓ Service doesn't block login on failure
- ✓ Service succeeds after xfsettingsd becomes available

---

### Test 4: Diagnostic Script

**Preconditions:** Service installed

**Steps:**
1. Run diagnostic script: `./scripts/check-hotkey-status.sh`
2. Review output for:
   - Service status
   - xfconf registration status
   - xfsettingsd process check
   - Recent logs
3. Stop service: `systemctl --user stop dictation-hotkey.service`
4. Run diagnostic again
5. Verify diagnostic detects inactive service

**Expected Results:**
- ✓ Diagnostic shows comprehensive status
- ✓ All checks pass when service running
- ✓ Diagnostic clearly indicates issues when service stopped
- ✓ Troubleshooting tips provided in output

---

### Test 5: Uninstallation

**Preconditions:** Service installed and running

**Steps:**
1. Run unregistration: `./scripts/unregister-hotkey.sh`
2. Verify hotkey removed from xfconf-query
3. Test hotkey: Ctrl+' should not trigger dictation
4. Disable service: `systemctl --user disable dictation-hotkey.service`
5. Stop service: `systemctl --user stop dictation-hotkey.service`
6. Verify service disabled: `systemctl --user is-enabled dictation-hotkey.service` (should show "disabled")
7. Optionally remove files:
   - `rm ~/.config/systemd/user/dictation-hotkey.service`
   - `rm ~/.local/bin/{register,unregister}-hotkey.sh`

**Expected Results:**
- ✓ Hotkey unregistered successfully
- ✓ Service disabled and stopped
- ✓ System returns to pre-installation state
- ✓ No errors during uninstallation

---

## Tasks / Subtasks

### Task 1: Create Systemd Service Definition (AC: 1)
- [ ] Create `systemd/dictation-hotkey.service` with unit definition
  - [ ] Set `Description=Dictation Keyboard Shortcut Registration`
  - [ ] Set `After=graphical-session.target` (ensures GUI ready)
  - [ ] Set `Type=oneshot` (runs once per login)
  - [ ] Set `RemainAfterExit=yes` (maintains active state)
  - [ ] Set `ExecStart=%h/.local/bin/register-hotkey.sh` (%h = $HOME)
  - [ ] Set `WantedBy=default.target` (user session target)
  - [ ] Add documentation comments in service file

### Task 2: Create Registration Script (AC: 2)
- [ ] Create `scripts/register-hotkey.sh` with full functionality
  - [ ] Add shebang and error handling (`set -euo pipefail`)
  - [ ] Detect project root dynamically (resolve symlinks)
  - [ ] Wait for xfsettingsd availability (30 second timeout loop)
    - [ ] Use `pgrep xfsettingsd` or `ps aux | grep xfsettingsd`
    - [ ] Sleep 1 second between retries
    - [ ] Exit with error if timeout
  - [ ] Register hotkey via xfconf-query:
    - [ ] Channel: `xfce4-keyboard-shortcuts`
    - [ ] Property: `/commands/custom/<Primary>apostrophe`
    - [ ] Value: `{project_root}/scripts/dictation-toggle.sh` (absolute path)
    - [ ] Use `-n -t string -s` flags
  - [ ] Reload xfsettingsd: `pkill -HUP xfsettingsd`
  - [ ] Verify registration via xfconf-query readback
  - [ ] Log all operations for journalctl (echo to stdout)
  - [ ] Exit with appropriate exit codes (0=success, 1=failure)

### Task 3: Create Unregistration Script (AC: 3)
- [ ] Create `scripts/unregister-hotkey.sh`
  - [ ] Remove xfconf-query property: `xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe" -r`
  - [ ] Reload xfsettingsd: `pkill -HUP xfsettingsd`
  - [ ] Log operations
  - [ ] Handle errors gracefully (property not found, xfsettingsd not running)

### Task 4: Create Installation Helper Script (AC: 4)
- [ ] Create `scripts/install-hotkey-service.sh`
  - [ ] Create systemd user directory: `mkdir -p ~/.config/systemd/user`
  - [ ] Create bin directory: `mkdir -p ~/.local/bin`
  - [ ] Copy service file to `~/.config/systemd/user/dictation-hotkey.service`
  - [ ] Copy registration script to `~/.local/bin/register-hotkey.sh`
  - [ ] Copy unregistration script to `~/.local/bin/unregister-hotkey.sh`
  - [ ] Set executable permissions: `chmod +x ~/.local/bin/{register,unregister}-hotkey.sh`
  - [ ] Reload systemd: `systemctl --user daemon-reload`
  - [ ] Enable service: `systemctl --user enable dictation-hotkey.service`
  - [ ] Start service: `systemctl --user start dictation-hotkey.service`
  - [ ] Verify service status and display to user
  - [ ] Show next steps (reboot to verify persistence)

### Task 5: Create Diagnostic Script (AC: 5)
- [ ] Create `scripts/check-hotkey-status.sh`
  - [ ] Check systemd service status: `systemctl --user status dictation-hotkey.service`
  - [ ] Check if xfsettingsd running: `pgrep xfsettingsd`
  - [ ] Check xfconf registration: `xfconf-query -c xfce4-keyboard-shortcuts -l | grep apostrophe`
  - [ ] Show recent logs: `journalctl --user -u dictation-hotkey.service -n 20`
  - [ ] Provide troubleshooting tips based on status
  - [ ] Format output clearly with sections and status indicators

### Task 6: Integration Testing (AC: 6, 7, 8, 9)
- [ ] Run Test 1: Clean installation
- [ ] Run Test 2: Reboot persistence (3 consecutive reboots)
- [ ] Run Test 3: Service failure handling
- [ ] Run Test 4: Diagnostic script functionality
- [ ] Run Test 5: Uninstallation
- [ ] Verify all existing functionality unchanged:
  - [ ] Test audio recording quality
  - [ ] Test transcription accuracy
  - [ ] Test text injection behavior
  - [ ] Test lock file mechanism
  - [ ] Test notifications

### Task 7: Documentation (AC: 10)
- [ ] Update `README.md` with systemd service section
  - [ ] Add installation instructions
  - [ ] Add verification steps
  - [ ] Add uninstallation instructions
- [ ] Create troubleshooting section in README or separate doc
  - [ ] Service not starting
  - [ ] Hotkey not working after reboot
  - [ ] xfsettingsd issues
  - [ ] XFCE detection problems
- [ ] Update `docs/MIGRATION-TO-UV.md` with systemd service info
- [ ] Document service in `docs/architecture/` if applicable

---

## Dev Notes

### Critical Information from Epic and Architecture

**Epic Reference:** [docs/epics/epic-uv-migration.md](../epics/epic-uv-migration.md) (Lines 117-153)

**This is Story 2 of 3-story epic for UV migration:**
- **Story 8 (UV Migration):** ✅ COMPLETE - Package structure migrated
- **Story 9 (This Story):** Systemd Service & Hotkey Persistence
- **Story 10 (Future):** Advanced Configuration, Testing & Documentation

**Brownfield Context:**

This addresses the #1 user pain point: **100% hotkey persistence failure rate** across reboots. The issue is well-documented in `docs/current-state.md` (lines 557-585).

**Root Cause (Confirmed):**
- `xfconf-query` successfully writes XML configuration
- `xfsettingsd` daemon doesn't reload configuration automatically
- No native xfconf-query reload command exists
- Manual daemon restart is risky (affects entire user session)

**Solution Pattern: Systemd User Service**

Systemd user services run in user context (not root) and are perfect for:
- Running on login (graphical-session.target)
- Waiting for dependencies (xfsettingsd)
- Graceful reload signals (SIGHUP)
- Comprehensive logging (journalctl)
- Enable/disable/status management

### Technical Context from Current State

**Source:** [docs/current-state.md](../current-state.md) (Lines 524-585)

**Current Hotkey Registration Process (setup.sh lines 308-371):**

1. Interactive hotkey selection (default: `<Primary>apostrophe`)
2. xfconf-query command:
   ```bash
   xfconf-query -c xfce4-keyboard-shortcuts \
       -p "/commands/custom/$hotkey" \
       -n -t string \
       -s "$script_path"
   ```
3. Success verification (readback)
4. Display to user

**The Missing Piece:** Reload signal to xfsettingsd

### XFCE Settings Daemon (xfsettingsd)

**Purpose:** Monitors xfconf configuration and applies changes to desktop environment

**Process Management:**
- Started automatically by XFCE session manager
- Runs continuously in background
- PID findable via: `pgrep xfsettingsd` or `ps aux | grep xfsettingsd`

**Reload Mechanism:**
- `SIGHUP` signal causes graceful reload without restart
- Command: `pkill -HUP xfsettingsd`
- This is **SAFE** - doesn't kill process, just reloads config
- Used extensively in system services (nginx, sshd, etc.)

**Why Not Kill/Restart:**
- `pkill xfsettingsd` kills daemon entirely
- May affect other XFCE settings being applied
- Session manager may auto-restart (race condition)
- SIGHUP is the standard pattern for config reload

### Systemd User Service Architecture

**User vs System Services:**
- **System services:** `/etc/systemd/system/` (require root)
- **User services:** `~/.config/systemd/user/` (user context)
- User services run only when user logged in
- Perfect for desktop environment integrations

**Service Lifecycle:**
```
User Login
  ↓
graphical-session.target reached
  ↓
dictation-hotkey.service starts (After=graphical-session.target)
  ↓
ExecStart runs: register-hotkey.sh
  ↓
Script waits for xfsettingsd (max 30s)
  ↓
Script runs xfconf-query
  ↓
Script sends SIGHUP to xfsettingsd
  ↓
Script verifies registration
  ↓
Service enters "active (exited)" state (RemainAfterExit=yes)
```

**RemainAfterExit=yes Explanation:**
- `oneshot` services normally enter "inactive" after ExecStart completes
- `RemainAfterExit=yes` keeps them in "active" state
- This indicates "I successfully ran and my effect persists"
- Service won't restart automatically (oneshot runs once)

### Script Design Patterns

**1. Wait for Dependency (xfsettingsd):**

```bash
# Wait for xfsettingsd (max 30 seconds)
TIMEOUT=30
WAITED=0
while ! pgrep -x xfsettingsd > /dev/null; do
    if [ $WAITED -ge $TIMEOUT ]; then
        echo "ERROR: xfsettingsd not available after ${TIMEOUT}s" >&2
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done
echo "xfsettingsd detected (waited ${WAITED}s)"
```

**2. Project Root Detection:**

```bash
# Detect project root (works from any script location)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOGGLE_SCRIPT="${PROJECT_ROOT}/scripts/dictation-toggle.sh"
```

**3. Logging for Systemd Journal:**

```bash
# Systemd captures stdout/stderr to journal
echo "Starting hotkey registration..."
echo "Project root: $PROJECT_ROOT"

# Errors to stderr (shown in red in journalctl -x)
echo "ERROR: xfconf-query failed" >&2
```

**4. Exit Codes:**

```bash
# 0 = success, service shows "active (exited)"
# 1+ = failure, service shows "failed"
exit 0  # Success
exit 1  # General error
exit 2  # Timeout error
```

### xfconf-query Command Reference

**Register Hotkey:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
    -p "/commands/custom/<Primary>apostrophe" \
    -n -t string \
    -s "/absolute/path/to/scripts/dictation-toggle.sh"
```

**Verify Registration:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
    -p "/commands/custom/<Primary>apostrophe"
# Should output: /absolute/path/to/scripts/dictation-toggle.sh
```

**Remove Registration:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
    -p "/commands/custom/<Primary>apostrophe" \
    -r
```

**List All Custom Commands:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts -l | grep "/commands/custom/"
```

**Flags:**
- `-c CHANNEL`: Configuration channel (xfce4-keyboard-shortcuts)
- `-p PROPERTY`: Property path (must start with /)
- `-n`: Create new property
- `-t TYPE`: Property type (string, int, bool, etc.)
- `-s VALUE`: Set value
- `-r`: Remove property

### File Locations (XDG Compliant)

**Service Files:**
- Service definition: `systemd/dictation-hotkey.service` (repository)
- Installed location: `~/.config/systemd/user/dictation-hotkey.service`

**Scripts:**
- Source: `scripts/register-hotkey.sh`, `scripts/unregister-hotkey.sh` (repository)
- Installed: `~/.local/bin/register-hotkey.sh`, `~/.local/bin/unregister-hotkey.sh`
- Why `~/.local/bin/`: Standard location for user executables (in PATH on most distros)

**Logs:**
- View with: `journalctl --user -u dictation-hotkey.service`
- Follow live: `journalctl --user -u dictation-hotkey.service -f`
- Last 20 lines: `journalctl --user -u dictation-hotkey.service -n 20`
- Since boot: `journalctl --user -u dictation-hotkey.service -b`

### Integration with Existing Setup

**Current Setup Flow (setup.sh):**
1. Check system dependencies (portaudio, xdotool, libnotify)
2. Create UV environment: `uv sync --extra dictation`
3. Register hotkey via xfconf-query (Lines 308-371)
4. Display post-installation checklist

**Enhanced Setup Flow (After This Story):**
1. Check system dependencies
2. Create UV environment
3. **Install systemd service:** `./scripts/install-hotkey-service.sh`
4. Display verification steps (reboot to test persistence)

**Backwards Compatibility:**
- Systemd service installation is **optional**
- Users can still manually register via xfconf-query
- If service not installed, old behavior remains
- No breaking changes to existing installations

### Testing Requirements

**Critical Tests:**
1. **3 Consecutive Reboots:** Must validate hotkey persists across multiple restarts
2. **Timing:** Hotkey must work within 5 seconds of login
3. **Failure Handling:** Service must not block login if xfsettingsd unavailable
4. **Logs:** Must be accessible via journalctl for troubleshooting

**Manual Testing Checklist:**
- [ ] Fresh installation on clean system
- [ ] Service enables correctly
- [ ] Hotkey works immediately after installation
- [ ] Reboot 1: Hotkey works
- [ ] Reboot 2: Hotkey works
- [ ] Reboot 3: Hotkey works
- [ ] Service logs are clear and informative
- [ ] Diagnostic script provides useful output
- [ ] Uninstallation cleans up completely

### Known Risks and Mitigations

**Risk 1: xfsettingsd Not Available at Login**
- **Mitigation:** 30-second timeout with clear error message
- **Fallback:** Service fails gracefully, user can manually register
- **Impact:** Low - rare condition, clear troubleshooting path

**Risk 2: SIGHUP Reload Doesn't Work**
- **Mitigation:** Verify xfsettingsd supports SIGHUP (standard behavior)
- **Fallback:** Document manual restart procedure
- **Testing:** Verify reload signal works before finalizing

**Risk 3: Non-XFCE Environments**
- **Mitigation:** Detect xfsettingsd availability before registration
- **Fallback:** Exit gracefully with informative message
- **Documentation:** Clearly state XFCE requirement in README

**Risk 4: Systemd User Service Not Supported**
- **Mitigation:** Check systemctl --user availability in install script
- **Fallback:** Provide manual registration instructions
- **Impact:** Very low - systemd user services standard since systemd 226 (2015)

**Risk 5: Service Runs But Hotkey Still Doesn't Persist**
- **Mitigation:** Comprehensive verification in registration script
- **Diagnostic:** check-hotkey-status.sh helps debug
- **Documentation:** Troubleshooting guide covers this scenario

### Systemd Commands Reference

**User Service Management:**

```bash
# Reload daemon after adding/modifying service files
systemctl --user daemon-reload

# Enable service (start on login)
systemctl --user enable dictation-hotkey.service

# Start service immediately
systemctl --user start dictation-hotkey.service

# Check status
systemctl --user status dictation-hotkey.service

# View logs
journalctl --user -u dictation-hotkey.service

# Stop service
systemctl --user stop dictation-hotkey.service

# Disable service (won't start on login)
systemctl --user disable dictation-hotkey.service

# Restart service
systemctl --user restart dictation-hotkey.service

# Check if enabled
systemctl --user is-enabled dictation-hotkey.service

# Check if active
systemctl --user is-active dictation-hotkey.service
```

### Performance Considerations

**Service Startup Time:**
- Target: < 5 seconds from login to hotkey active
- Wait loop: 1 second intervals (minimal overhead)
- xfconf-query: Near-instant (< 100ms)
- pkill -HUP: Instant signal delivery
- Total expected: 1-2 seconds (assuming xfsettingsd already running)

**Impact on Login:**
- Service runs in background (doesn't block login)
- User can start using desktop immediately
- Hotkey becomes available within seconds
- No noticeable delay

### Troubleshooting Guide (For Documentation)

**Issue: Service shows "failed" status**

Check logs:
```bash
journalctl --user -u dictation-hotkey.service -n 50
```

Common causes:
1. xfsettingsd not running (timeout)
2. xfconf-query command failed (permissions, missing channel)
3. Script not executable (permissions)

**Issue: Hotkey doesn't work after reboot**

Verify registration:
```bash
xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe"
```

Check xfsettingsd:
```bash
pgrep xfsettingsd
```

Manually reload:
```bash
pkill -HUP xfsettingsd
```

**Issue: Service not starting on login**

Check if enabled:
```bash
systemctl --user is-enabled dictation-hotkey.service
```

Check systemd user instance running:
```bash
systemctl --user status
```

**Issue: Multiple xfsettingsd processes**

Kill all and let session manager restart:
```bash
pkill xfsettingsd
# XFCE session manager will auto-restart
```

### Development Environment Setup

**Testing Systemd User Services:**

```bash
# Edit service file
vim systemd/dictation-hotkey.service

# Edit registration script
vim scripts/register-hotkey.sh

# Install for testing (manual method)
mkdir -p ~/.config/systemd/user
mkdir -p ~/.local/bin
cp systemd/dictation-hotkey.service ~/.config/systemd/user/
cp scripts/register-hotkey.sh ~/.local/bin/
chmod +x ~/.local/bin/register-hotkey.sh
systemctl --user daemon-reload

# Test immediately (without waiting for login)
systemctl --user start dictation-hotkey.service

# Check result
systemctl --user status dictation-hotkey.service
journalctl --user -u dictation-hotkey.service -n 20

# Enable for next login
systemctl --user enable dictation-hotkey.service
```

**Rapid Iteration:**

```bash
# Make changes to script
vim scripts/register-hotkey.sh

# Copy to installed location
cp scripts/register-hotkey.sh ~/.local/bin/

# Restart service to test
systemctl --user restart dictation-hotkey.service

# Check logs
journalctl --user -u dictation-hotkey.service -n 10
```

### Reference Files

**Existing Scripts to Reference:**
- `scripts/dictation-toggle.sh` (Lines 1-60) - Current toggle wrapper with UV
- `modules/dictation/setup.sh` (Lines 307-357) - Current xfconf-query registration
- `docs/current-state.md` (Lines 557-585) - Root cause analysis

**Configuration Files:**
- XFCE shortcuts config: `~/.config/xfce4/xfconf/xfce4-keyboard-shortcuts/xfce4-keyboard-shortcuts.xml`
- System dependencies: `docs/architecture/SYSTEM_DEPS.md`

**Related Stories:**
- Story 8 (UV Migration): [docs/stories/story-8-uv-migration.md](./story-8-uv-migration.md) - COMPLETE
- Epic: [docs/epics/epic-uv-migration.md](../epics/epic-uv-migration.md)

---

## Definition of Done

- ✅ Systemd service file created and documented
- ✅ Registration script created with full functionality
- ✅ Unregistration script created for cleanup
- ✅ Installation helper script created and tested
- ✅ Diagnostic script created for troubleshooting
- ✅ All acceptance tests pass (Tests 1-5)
- ✅ Hotkey persists across 3 consecutive reboots (validated)
- ✅ Service logs are clear and accessible via journalctl
- ✅ Existing dictation functionality unchanged (no regressions)
- ✅ Documentation updated (README, troubleshooting guide)
- ✅ Code reviewed (if applicable)
- ✅ Committed to version control with clear commit messages

---

## Related Documents

- **Epic:** [docs/epics/epic-uv-migration.md](../epics/epic-uv-migration.md)
- **Previous Story:** [docs/stories/story-8-uv-migration.md](./story-8-uv-migration.md) (COMPLETE)
- **Current State Analysis:** [docs/current-state.md](../current-state.md) (Lines 557-585)
- **System Dependencies:** [docs/architecture/SYSTEM_DEPS.md](../architecture/SYSTEM_DEPS.md)
- **Hotkey Registration:** `modules/dictation/setup.sh` (Lines 307-357)
- **Toggle Script:** `scripts/dictation-toggle.sh`

---

## Notes for Developer

**Implementation Priority:**
1. Start with registration script (core logic)
2. Test registration script manually
3. Create systemd service file
4. Test service manually (systemctl --user start)
5. Create installation helper
6. Test full installation flow
7. Reboot test (critical validation)
8. Create diagnostic and unregistration scripts
9. Documentation

**Common Pitfalls to Avoid:**
1. **Absolute paths:** Service must use absolute paths (no relative paths)
2. **Permissions:** Scripts must be executable (chmod +x)
3. **SIGHUP syntax:** Use `pkill -HUP` not `pkill -s HUP`
4. **Timeout handling:** Don't wait forever for xfsettingsd
5. **Exit codes:** 0=success, 1+=failure for systemd

**Debugging Tips:**
- `journalctl --user -u dictation-hotkey.service -f` (follow logs live)
- `systemctl --user status dictation-hotkey.service -l` (full output)
- Test scripts directly: `bash -x ~/.local/bin/register-hotkey.sh` (debug mode)
- Check xfsettingsd: `ps aux | grep xfsettingsd`

**Time Estimates:**
- Task 1 (Service File): 30 minutes
- Task 2 (Registration Script): 1.5 hours
- Task 3 (Unregistration Script): 30 minutes
- Task 4 (Installation Script): 1 hour
- Task 5 (Diagnostic Script): 1 hour
- Task 6 (Integration Testing): 1.5 hours
- Task 7 (Documentation): 1 hour
- **Total:** 5.5-7 hours (including testing and iteration)

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-28 | 1.0 | Initial brownfield story creation from epic | Bob (Scrum Master) |

---

**Story Status:** Draft  
**Awaiting:** Developer assignment and approval  
**Next Story:** Story 10 - Advanced Configuration, Testing & Documentation (Epic Story 3)

