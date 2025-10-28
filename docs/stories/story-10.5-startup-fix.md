# Story 10.5: Ensure Dictation Works on First Run After Restart - Brownfield Bug Fix

## User Story

As a **dictation system user**,  
I want **the dictation system to work immediately on first use after system restart**,  
So that **I don't have to manually sync UV environment or troubleshoot failures before dictation becomes usable**.

---

## Story Context

### Existing System Integration

- **Integrates with:** Story 9 systemd hotkey registration service (`dictation-hotkey.service`)
- **Technology:** Bash script (`scripts/dictation-toggle.sh`), UV package manager, systemd user services
- **Follows pattern:** Existing error handling patterns in `dictation-toggle.sh` (notify-send, validation checks)
- **Touch points:** 
  - `scripts/dictation-toggle.sh` (main integration point - needs UV health check)
  - UV environment (`.venv/` managed by UV)
  - systemd service trigger flow (hotkey → toggle script → UV → Python module)

### Problem Statement

Story 9 successfully registers the hotkey on startup, but **dictation fails on first use after restart** because the UV environment may not be synced when the hotkey is triggered for the first time.

**Current Behavior:**
1. User reboots system
2. Logs in → systemd service registers hotkey successfully ✅
3. Presses `Ctrl+'` → `dictation-toggle.sh` runs
4. ❌ **Fails** because UV environment not ready (`uv run` fails with missing dependencies)

**Root Cause:** UV's virtual environment (`.venv/`) may be out of sync, corrupted, or missing after a fresh boot, causing `uv run` to fail before Python module can execute.

---

## Acceptance Criteria

### Functional Requirements

1. **Dictation works on first use after system restart**
   - No manual `uv sync` required before first hotkey press
   - User receives immediate dictation functionality or clear error message

2. **Script performs automatic UV environment health check**
   - Validates `.venv/` exists and is accessible
   - Checks for lock file (`uv.lock`) consistency
   - Syncs environment automatically if needed

3. **Comprehensive logging for troubleshooting**
   - All operations logged to `/tmp/dictation-toggle.log`
   - Timestamps, operation types, success/failure status
   - UV sync output captured when sync occurs

### Integration Requirements

4. **Existing systemd service continues to work unchanged**
   - `dictation-hotkey.service` registration flow unaffected
   - No changes required to `register-hotkey.sh` or service definition

5. **New functionality follows existing error handling pattern**
   - Uses `notify-send` for user-facing error messages
   - Follows same validation approach as existing UV/pyproject.toml checks
   - Error exit codes maintain consistency (exit 1 for failures)

6. **Integration with UV maintains current behavior**
   - `uv run` execution path preserved
   - No changes to Python module invocation
   - Environment variable handling unchanged

### Quality Requirements

7. **Performance targets met**
   - **First run after restart:** < 5 seconds (including sync if needed)
   - **Subsequent runs:** < 1 second (no sync needed)
   - UV sync only triggered when necessary (lazy evaluation)

8. **Error notifications are user-friendly**
   - Clear description of failure (e.g., "UV sync failed")
   - Actionable instructions (e.g., "Check /tmp/dictation-toggle.log")
   - Critical priority for blocking issues

9. **Solution works across multiple restart cycles**
   - Tested across 3+ consecutive reboots
   - No regression in existing functionality verified
   - Idempotent behavior (repeated runs safe)

---

## Technical Notes

### Integration Approach

Enhance `scripts/dictation-toggle.sh` with pre-flight UV environment validation:

1. **Add health check function before `uv run` execution:**
   - Check if `.venv/` directory exists
   - Validate `uv.lock` file is present and readable
   - Optional: Quick validation via `uv run python -c "import sys; sys.exit(0)"`

2. **Add automatic sync with logging:**
   - Run `uv sync` if health check fails
   - Capture output to log file
   - Show progress notification to user (optional)

3. **Add logging infrastructure:**
   - Log file: `/tmp/dictation-toggle.log`
   - Timestamp format: ISO 8601 (`date -Iseconds`)
   - Log rotation not required (ephemeral `/tmp` location)

### Existing Pattern Reference

Follow existing validation pattern in `dictation-toggle.sh`:

```23:30:scripts/dictation-toggle.sh
if ! command -v uv &> /dev/null; then
    if command -v notify-send &> /dev/null; then
        notify-send -u critical "Dictation Error" "UV not found. Please install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    echo "ERROR: UV not found in PATH" >&2
    echo "Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi
```

Apply same structure for UV sync check and error handling.

### Key Constraints

- **No changes to systemd service or registration scripts** (preserve Story 9 implementation)
- **Maintain backward compatibility** (existing manual usage patterns continue working)
- **Idempotent execution** (safe to run multiple times, sync only when needed)
- **No external dependencies** (pure bash, UV, and system tools only)
- **Log file location non-configurable** (`/tmp/dictation-toggle.log` hardcoded for simplicity)

### Implementation Pseudocode

```bash
# After UV and pyproject.toml validation (line ~40)

LOG_FILE="/tmp/dictation-toggle.log"

log_message() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# Health check function
check_uv_environment() {
    log_message "INFO: Checking UV environment health..."
    
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        log_message "WARN: .venv directory missing, triggering sync..."
        return 1
    fi
    
    if [ ! -f "$PROJECT_ROOT/uv.lock" ]; then
        log_message "WARN: uv.lock missing, triggering sync..."
        return 1
    fi
    
    # Quick validation: attempt to import Python
    if ! uv run python -c "import sys; sys.exit(0)" &>> "$LOG_FILE"; then
        log_message "WARN: UV environment validation failed, triggering sync..."
        return 1
    fi
    
    log_message "INFO: UV environment healthy"
    return 0
}

# Sync function
sync_uv_environment() {
    log_message "INFO: Syncing UV environment..."
    
    if ! uv sync &>> "$LOG_FILE"; then
        log_message "ERROR: UV sync failed"
        notify-send -u critical "Dictation Error" "UV sync failed. Check /tmp/dictation-toggle.log"
        return 1
    fi
    
    log_message "INFO: UV sync completed successfully"
    return 0
}

# Main pre-flight check
if ! check_uv_environment; then
    if ! sync_uv_environment; then
        exit 1
    fi
fi

# Proceed to existing execution (line 58)
exec uv run -m automation_scripts.dictation --toggle
```

---

## Definition of Done

- [x] Functional requirements met (dictation works on first run after restart)
- [x] Integration requirements verified (systemd service unchanged, error patterns consistent)
- [x] Existing functionality regression tested (manual dictation usage still works)
- [x] Code follows existing patterns and standards (bash validation pattern, notify-send usage)
- [x] Tests pass (manual testing across multiple reboot cycles)
- [x] Documentation updated if applicable (README troubleshooting section may need update)

---

## Risk and Compatibility Check

### Minimal Risk Assessment

**Primary Risk:** UV sync operation takes too long (> 5 seconds), causing user frustration on first run

**Mitigation:**
- Add progress notification during sync: `notify-send -t 3000 "Dictation" "Initializing environment, please wait..."`
- UV sync is typically fast (< 3s for dictation module)
- Lazy evaluation ensures sync only runs when necessary

**Rollback:** Simple - revert `scripts/dictation-toggle.sh` to previous version (git checkout)

### Compatibility Verification

- [x] **No breaking changes to existing APIs:** Script interface unchanged (hotkey trigger path identical)
- [x] **Database changes:** N/A (no database involved)
- [x] **UI changes follow existing design patterns:** Uses existing `notify-send` pattern
- [x] **Performance impact is negligible:** < 5s first run (acceptable), < 1s subsequent (no impact)

---

## Scope Validation

- [x] **Story can be completed in one development session:** Estimated 1-2 hours
- [x] **Integration approach is straightforward:** Single file modification (`dictation-toggle.sh`)
- [x] **Follows existing patterns exactly:** Mirrors existing validation structure
- [x] **No design or architecture work required:** Pure implementation following established patterns

---

## Priority and Estimation

**Priority:** **HIGH** (blocks Story 9 usability - user cannot use dictation without manual intervention)

**Estimate:** **1-2 hours** (including testing across multiple restart cycles)

**Effort Breakdown:**
- Implementation: 30-45 minutes
- Testing (3+ reboot cycles): 30-45 minutes
- Documentation updates: 15-30 minutes

---

## Related Work

- **Depends on:** Story 9 (systemd hotkey registration service)
- **Blocks:** None (enables immediate usability after restart)
- **Related:** Epic: UV Migration (ensures UV-based workflow is fully robust)

---

_Story created via *create-brownfield-story command by John (PM Agent)_

