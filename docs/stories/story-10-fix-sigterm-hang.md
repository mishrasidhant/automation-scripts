# Story 10: Fix Dictation SIGTERM Hang - Brownfield Bug Fix

## User Story

As a **dictation user**,
I want **the recording to stop gracefully when I toggle dictation off**,
So that **my spoken words are transcribed and pasted successfully without errors or timeouts**.

---

## Story Context

**Existing System Integration:**

- Integrates with: Dictation recording module (`src/automation_scripts/dictation/dictate.py`)
- Technology: Python, sounddevice (PortAudio), signal handling, subprocess management
- Follows pattern: Signal-based process lifecycle management (SIGTERM → cleanup → exit)
- Touch points: Audio stream management (sounddevice), file I/O (`_save_audio_data()`), process signaling (stop command → recording process)

**Bug Reference:** 
- Bug ID: DICT-BUG-001
- Severity: CRITICAL
- Full Report: `docs/bugs/CRITICAL-BUG-DICTATION-SIGTERM.md`
- Discovered During: Story 9 testing (hotkey functionality itself works correctly)

**Current Behavior:**
Recording process receives SIGTERM, signal handler begins execution, but hangs during audio stream cleanup (`stream.stop()`/`stream.close()`) or file saving (`_save_audio_data()`), resulting in 5-second timeout followed by SIGKILL and "Failed to stop recording" error.

---

## Acceptance Criteria

### Functional Requirements:

1. Recording starts successfully when user triggers dictation (already working)
2. Recording stops within 1 second when SIGTERM is received (no 5-second timeout)
3. Audio file is saved successfully to `/tmp/dictation/` directory
4. Lock file (`/tmp/dictation.lock`) is removed cleanly after stop
5. Transcription completes successfully using Whisper API
6. Transcribed text is pasted to the active window cursor position
7. Process exits with code 0 on successful stop (not code 1)

### Integration Requirements:

8. Existing recording start functionality continues to work unchanged
9. New stop mechanism follows existing signal-based process control pattern
10. Integration with Story 9 hotkey (Ctrl+') maintains current behavior
11. Lock file management remains consistent with existing implementation
12. No changes to transcription or paste logic required (they should "just work" once audio saves)

### Quality Requirements:

13. Works reliably with short recordings (1-2 seconds of audio)
14. Works reliably with long recordings (30+ seconds of audio)
15. No zombie processes remain after stop
16. No stale lock files remain after stop or failure
17. SIGINT (Ctrl+C) handling continues to work correctly
18. Change is covered by appropriate tests (manual testing checklist provided)
19. No regression in existing dictation functionality verified

---

## Technical Notes

### Integration Approach:

The fix must address the hang in the signal handler without disrupting the existing architecture. Three strategies are available (from bug report):

1. **Option 1: Graceful Stream Shutdown (Recommended)** - Add timeout protection around `stream.stop()` and `stream.close()` using threading
2. **Option 2: Async Signal Handling** - Use flag-based approach where signal handler sets flag and main loop performs cleanup
3. **Option 3: Separate Stop Process** - Use IPC (control file) instead of SIGTERM for stop requests

**Recommendation:** Start with Option 1 (timeout protection) as it requires minimal architectural changes and maintains existing signal-based pattern.

### Existing Pattern Reference:

- Signal handler pattern: Lines 720-740 in `dictate.py`
- Stop method pattern: Lines 633-667 in `dictate.py`
- Current timeout: 5 seconds (50 iterations × 0.1s sleep)
- Target timeout: 1-2 seconds maximum

### Key Constraints:

- Must maintain backward compatibility with existing command-line interface (`--start`, `--stop`, `--toggle`)
- Must not break Story 9 hotkey integration (systemd service + Ctrl+' hotkey)
- Must preserve all existing error handling and notification patterns
- Audio stream cleanup must be thread-safe
- File I/O must complete or timeout gracefully

### Investigation Steps Already Completed:

- Root cause identified: Hang occurs during signal handler execution
- Signal handler definitely executes (log message confirmed)
- Process receives SIGTERM successfully
- Hang location isolated to: `stream.stop()`, `stream.close()`, or `_save_audio_data()`
- Three fix strategies proposed and documented

---

## Definition of Done

- [ ] Signal handler executes and completes within 1 second (no timeout)
- [ ] Audio file saves successfully to disk
- [ ] Lock file removed cleanly after stop
- [ ] Process exits with code 0 on successful stop
- [ ] Transcription completes and text pastes to active window
- [ ] No SIGKILL required to terminate process
- [ ] Tested with short recordings (1-2 seconds)
- [ ] Tested with long recordings (30+ seconds)
- [ ] No zombie processes remain
- [ ] No stale lock files remain
- [ ] Existing functionality regression tested (start, hotkey, notifications)
- [ ] Code follows existing patterns and standards
- [ ] Manual testing checklist from bug report completed

---

## Risk and Compatibility Check

### Minimal Risk Assessment:

**Primary Risk:** Timeout protection or flag-based approach could introduce race conditions or prevent proper cleanup in edge cases.

**Mitigation:** 
- Use well-tested threading patterns for timeout implementation
- Add comprehensive logging at each step of cleanup process
- Test with various recording lengths and rapid start/stop cycles
- Keep signal handler logic minimal (set flags, don't do complex work)

**Rollback:** 
- If fix causes regressions, git revert the commit
- No database or external state changes involved
- Lock file and audio files are temporary (`/tmp/`) and can be manually cleaned

### Compatibility Verification:

- [x] No breaking changes to existing APIs (internal module only)
- [x] No database changes (no database involved)
- [x] No UI changes (follows existing notification patterns)
- [x] Performance impact is negligible (faster stop time = better UX)
- [x] No changes to public interfaces or command-line arguments

---

## Validation Checklist

### Scope Validation:

- [x] Story can be completed in one development session (2-4 hours estimated)
- [x] Integration approach is straightforward (fix signal handler or add flag-based stop)
- [x] Follows existing patterns (signal handling, timeout management)
- [x] No design or architecture work required (pattern selection provided)

### Clarity Check:

- [x] Story requirements are unambiguous (specific timeout values, exit codes, file operations)
- [x] Integration points are clearly specified (signal handler, stop method, audio stream)
- [x] Success criteria are testable (manual testing checklist in bug report)
- [x] Rollback approach is simple (git revert, manual cleanup if needed)

---

## Priority & Estimate

**Priority:** CRITICAL - Blocks all dictation usage

**Estimate:** 2-4 hours
- Investigation: COMPLETE (documented in bug report)
- Implementation: 1-2 hours (add timeout protection or flag-based stop)
- Testing: 1-2 hours (comprehensive testing checklist from bug report)

**Blocking:** All dictation functionality is unusable until this is fixed

---

## References

- **Bug Report:** `docs/bugs/CRITICAL-BUG-DICTATION-SIGTERM.md`
- **Affected File:** `src/automation_scripts/dictation/dictate.py`
- **Signal Handler:** Lines 720-740
- **Stop Method:** Lines 633-667
- **Related Story:** Story 9 (hotkey works correctly, not affected by this bug)

---

**Story Created:** 2025-10-28  
**Type:** Critical Bug Fix (Brownfield)  
**Created By:** John (PM Agent)

