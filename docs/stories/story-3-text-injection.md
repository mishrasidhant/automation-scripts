# Story 3: Text Injection & State Management

**Story ID:** DICT-003  
**Epic:** Dictation Module Implementation  
**Priority:** High (Core Functionality)  
**Complexity:** High  
**Estimated Effort:** 3-4 hours  
**Depends On:** Story 1 (Audio), Story 2 (Transcription)

---

## User Story

**As a** user who has recorded and transcribed speech,  
**I want** the transcribed text automatically typed at my cursor position,  
**So that** I can seamlessly insert dictated text into any application.

---

## Story Context

### Existing System Integration

- **Builds on:** Story 1 (audio recording) + Story 2 (transcription)
- **Technology:** xdotool for X11 text injection, lock file state management
- **Desktop Environment:** XFCE on X11
- **Follows pattern:** Toggle-based activation (start/stop with same trigger)

### Technical Approach

Complete the core `dictate.py` functionality:
- Implement toggle mode (`--toggle`) for start/stop with single command
- Integrate all components: record → transcribe → paste workflow
- Use lock file for state management (recording vs idle)
- Inject text using xdotool (X11 keyboard simulation)
- Clean up temporary files after completion

---

## Acceptance Criteria

### Functional Requirements

1. **Script implements toggle mode for user-friendly operation**
   - `python3 dictate.py --toggle` starts recording if not active
   - `python3 dictate.py --toggle` stops and transcribes if recording
   - Single command supports hotkey integration

2. **Lock file provides robust state management**
   - Lock file tracks current state (idle vs recording)
   - Lock file persists recording info (PID, audio file path, start time)
   - Stale lock files detected and cleaned up (orphaned processes)
   - Race conditions prevented (atomic lock file operations)

3. **Text injection works reliably in all applications**
   - Uses xdotool to type text at cursor position
   - Clears modifier keys before typing (prevents stuck keys)
   - Handles special characters correctly (spaces, punctuation)
   - Works in: terminal, text editor, browser, email client

### Integration Requirements

4. **Complete workflow executes seamlessly**
   - Toggle 1: Start recording + show notification
   - User speaks...
   - Toggle 2: Stop recording → transcribe → paste → cleanup
   - Total latency: <3 seconds from stop to paste (for 10s audio)

5. **Temporary files are cleaned up automatically**
   - Audio WAV file deleted after transcription (unless debug mode)
   - Lock file removed after successful completion
   - `/tmp/dictation/` directory managed (created if missing)

6. **Error recovery handles edge cases gracefully**
   - If transcription fails: notification shown, lock file cleaned up
   - If xdotool fails: text copied to clipboard as fallback
   - If process crashes: stale lock file detected on next run

### Quality Requirements

7. **Text pasting is accurate and reliable**
   - No characters lost or duplicated
   - Preserves punctuation and capitalization
   - Respects application input focus
   - Works with multi-byte characters (UTF-8)

8. **State management prevents race conditions**
   - Cannot start recording if already recording
   - Cannot stop if not recording (shows helpful message)
   - Lock file operations are atomic (no partial writes)

9. **User feedback covers all workflow stages**
   - Notification: "🎙️ Recording started..."
   - Notification: "⏳ Transcribing..." (with progress if possible)
   - Notification: "✅ Done! Pasted X words"
   - Notification: "❌ Error: [description]" (on failure)

---

## Technical Implementation Details

### Core Workflow State Machine

```
[IDLE]
  ↓ --toggle
[RECORDING] (lock file exists, audio stream active)
  ↓ --toggle
[TRANSCRIBING] (processing audio)
  ↓
[PASTING] (injecting text via xdotool)
  ↓
[CLEANUP] (remove files, lock file)
  ↓
[IDLE]
```

### Lock File Structure (Extended)

```json
{
  "pid": 12345,
  "state": "recording",
  "started_at": 1729900000,
  "audio_file": "/tmp/dictation/recording-12345.wav",
  "stream": {
    "device": "Blue Microphones",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

### Text Injection with xdotool

```python
def paste_text_xdotool(text: str) -> bool:
    """
    Inject text at cursor position using xdotool.
    
    Args:
        text: Text to type
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Clear any stuck modifier keys (Ctrl, Alt, etc.)
        subprocess.run(["xdotool", "keyup", "Control_L", "Alt_L", "Shift_L"],
                      check=False, capture_output=True)
        
        # Small delay to ensure keys are released
        time.sleep(0.05)
        
        # Type the text
        # --clearmodifiers: ensure no modifiers interfere
        # --delay: milliseconds between keystrokes (12ms default)
        # --: end of options, everything after is literal text
        result = subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return True
        
    except subprocess.TimeoutExpired:
        notify("Error: Text pasting timed out")
        return False
    except subprocess.CalledProcessError as e:
        notify(f"Error: xdotool failed - {e.stderr}")
        return False
```

### Toggle Logic Implementation

```python
def handle_toggle():
    """Handle toggle command: start if idle, stop if recording."""
    if lock_file_exists():
        # Stop recording workflow
        lock_data = read_lock_file()
        
        # Verify process is still running
        if not process_exists(lock_data["pid"]):
            notify("Cleaning up stale recording session...")
            cleanup_stale_lock()
            return
        
        # Stop audio recording
        stop_recording()
        
        # Transcribe audio
        notify("⏳ Transcribing...")
        text = transcribe_audio(lock_data["audio_file"])
        
        if not text:
            notify("❌ No speech detected")
            cleanup_lock_file()
            return
        
        # Paste text
        notify(f"📝 Pasting {len(text.split())} words...")
        if paste_text_xdotool(text):
            notify("✅ Done!")
        else:
            # Fallback: copy to clipboard
            copy_to_clipboard(text)
            notify("⚠️ Text copied to clipboard (paste manually)")
        
        # Cleanup
        cleanup_lock_file()
        if not DEBUG_MODE:
            delete_audio_file(lock_data["audio_file"])
    else:
        # Start recording workflow
        start_recording()
        create_lock_file()
        notify("🎙️ Recording started...")
```

---

## Implementation Checklist

### Phase 1: Toggle Mode Implementation
- [ ] Add `--toggle` argument to CLI parser
- [ ] Implement toggle logic (check lock file state)
- [ ] Wire up start/stop based on lock file presence
- [ ] Test toggle repeatedly (start, stop, start, stop)

### Phase 2: Text Injection with xdotool
- [ ] Install xdotool if not present
- [ ] Implement `paste_text_xdotool()` function
- [ ] Test typing in various apps (terminal, gedit, firefox)
- [ ] Handle special characters and multi-line text
- [ ] Add clipboard fallback for xdotool failures

### Phase 3: Complete Workflow Integration
- [ ] Chain: stop recording → transcribe → paste
- [ ] Add timing measurements for each stage
- [ ] Implement progress notifications
- [ ] Test full end-to-end workflow

### Phase 4: State Management & Cleanup
- [ ] Implement stale lock file detection
- [ ] Add atomic lock file operations
- [ ] Implement cleanup on success
- [ ] Implement cleanup on error
- [ ] Test with intentional crashes (kill -9)

### Phase 5: Error Handling & Edge Cases
- [ ] Handle: no audio input device
- [ ] Handle: transcription returns empty
- [ ] Handle: xdotool not installed
- [ ] Handle: no active window/cursor
- [ ] Handle: disk full (can't write temp files)

---

## Testing Strategy

### Unit Tests

```python
# Test lock file operations
def test_lock_file_creation_and_removal():
    # Create lock, verify exists, remove, verify gone
    pass

# Test stale lock detection
def test_stale_lock_cleanup():
    # Create lock with non-existent PID, verify cleanup
    pass

# Test text pasting
def test_xdotool_text_injection():
    # Type test text, verify it appears
    pass
```

### Integration Tests

```python
# Test full workflow
def test_complete_dictation_workflow():
    # Toggle start → record 5s → toggle stop
    # Verify text appears at cursor
    pass
```

### Manual Tests

1. **Basic Toggle Test**
   ```bash
   # Open text editor (gedit)
   gedit test.txt &
   
   # Click in editor window
   # Run toggle
   python3 dictate.py --toggle
   # Say: "This is a test"
   python3 dictate.py --toggle
   
   # Verify: "This is a test" appears in gedit
   ```

2. **Multi-Application Test**
   ```bash
   # Test in terminal
   python3 dictate.py --toggle
   # Speak command: "echo hello world"
   python3 dictate.py --toggle
   # Verify text appears in terminal
   
   # Test in browser
   firefox &
   # Navigate to text input field
   python3 dictate.py --toggle
   # Speak: "Testing in Firefox"
   python3 dictate.py --toggle
   # Verify text appears in browser
   ```

3. **Rapid Toggle Test**
   ```bash
   # Toggle 5 times in succession
   for i in {1..5}; do
     python3 dictate.py --toggle
     sleep 2
     python3 dictate.py --toggle
     sleep 1
   done
   # Verify: no lock file corruption, all iterations succeed
   ```

4. **Error Recovery Test**
   ```bash
   # Start recording
   python3 dictate.py --toggle
   
   # Kill process (simulate crash)
   ps aux | grep dictate.py
   kill -9 <PID>
   
   # Try to start again
   python3 dictate.py --toggle
   # Verify: detects stale lock, cleans up, starts fresh
   ```

5. **Special Characters Test**
   ```bash
   # Record text with punctuation
   python3 dictate.py --toggle
   # Say: "Hello! How are you? I'm fine, thanks."
   python3 dictate.py --toggle
   # Verify: punctuation appears correctly
   ```

6. **Long Text Test**
   ```bash
   # Record 30-60 seconds of continuous speech
   python3 dictate.py --toggle
   # Speak paragraph-length text
   python3 dictate.py --toggle
   # Verify: all text pasted, no truncation
   ```

---

## Definition of Done

- ✅ Toggle mode works: single command starts/stops dictation
- ✅ Lock file manages state reliably (no race conditions)
- ✅ Text injection works in multiple applications
- ✅ Complete workflow: record → transcribe → paste → cleanup
- ✅ Latency target met (<3s overhead for 10s audio)
- ✅ Stale lock files detected and cleaned up
- ✅ Error handling covers common failure modes
- ✅ Notifications provide clear feedback at each stage
- ✅ Manual tests pass in 5+ different applications
- ✅ No memory leaks or resource exhaustion on repeated use

---

## Dependencies

### System Dependencies
- xdotool (needs installation: `sudo pacman -S xdotool`)
- X11 (already present ✓)
- xclip or xsel (optional, for clipboard fallback)

### Python Dependencies
- All dependencies from Story 1 & 2 (already installed)

### Installation Commands
```bash
# Install xdotool
sudo pacman -S xdotool

# Optional: clipboard tools
sudo pacman -S xclip
```

---

## Example Usage (After Implementation)

```bash
# Complete end-to-end workflow
$ python3 dictate.py --toggle
🎙️ Recording started...

# (User speaks: "Hello, this is a dictation test.")

$ python3 dictate.py --toggle
⏳ Transcribing...
📝 Pasting 6 words...
✅ Done!

# Text "Hello, this is a dictation test." now appears at cursor

# Check status
$ cat /tmp/dictation.lock
# (File doesn't exist - already cleaned up)
```

---

## Performance Requirements

### Latency Breakdown (10 seconds of audio)

| Stage | Target | Notes |
|-------|--------|-------|
| Toggle command | <50ms | Script startup |
| Stop recording | <100ms | Close audio stream |
| Transcription | ~2.5s | base.en model, 4x RT |
| Text pasting | ~200ms | xdotool typing |
| Cleanup | <100ms | Delete files |
| **Total** | **~3s** | User-perceivable |

### Resource Usage

- **Memory:** ~600MB peak (during transcription)
- **CPU:** Spike during transcription (expected, temporary)
- **Disk:** ~1MB per recording (cleaned up)
- **Lock file:** <1KB

---

## Success Metrics

- **Functionality:** Complete workflow executes successfully
- **Reliability:** 95%+ success rate over 50 iterations
- **Performance:** Meets latency targets
- **Compatibility:** Works in 10+ different applications
- **User Experience:** Clear feedback, no confusion

---

## Technical Notes

### xdotool Typing Behavior

**Default typing delay:** 12ms between keystrokes
- Too fast (<5ms): Some apps may drop characters
- Too slow (>50ms): Noticeable typing animation
- 12ms: Good balance for most applications

**Modifier key clearing:** Essential to prevent:
- Ctrl+key being typed instead of plain text
- Alt+key triggering menu shortcuts
- Shift+key producing unexpected capitals

### Lock File Atomicity

**Write operation:**
```python
# Write to temp file, then atomic rename
with open(lock_file + ".tmp", "w") as f:
    json.dump(lock_data, f)
os.replace(lock_file + ".tmp", lock_file)  # Atomic on POSIX
```

**Read operation:**
```python
# Verify file exists and is valid JSON
if os.path.exists(lock_file):
    try:
        with open(lock_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Corrupted lock file, clean it up
        cleanup_stale_lock()
        return None
```

### Clipboard Fallback

If xdotool fails (rare, but possible):
```python
def copy_to_clipboard(text: str):
    """Fallback: copy text to clipboard."""
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # xclip not available, show text in notification
        notify(f"Text: {text[:50]}...")
```

---

## Risk Assessment

### Risks

1. **xdotool fails in specific application**
   - **Mitigation:** Clipboard fallback, test in common apps
   - **Likelihood:** Low (xdotool is very reliable on X11)

2. **Lock file race condition**
   - **Mitigation:** Atomic file operations, PID validation
   - **Likelihood:** Very Low (single-user scenario)

3. **Text pasting interrupted mid-typing**
   - **Mitigation:** xdotool timeout, user can undo/retry
   - **Likelihood:** Very Low

4. **Stale lock file prevents operation**
   - **Mitigation:** Automatic stale lock detection
   - **Likelihood:** Low (only on crashes)

### Rollback Plan

If text injection fails:
1. Text is in clipboard (if fallback worked)
2. Audio file preserved (if debug mode enabled)
3. User can manually transcribe/paste
4. Lock file cleaned up automatically

---

## Future Integration Points

This story completes the core `dictate.py` functionality, enabling:
- **Story 4:** Wrapper script can call `--toggle`
- **Story 5:** Setup script can validate text injection
- **Story 6:** End-to-end testing of complete workflow

---

## Related Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md` (Text injection section)
- **System Profile:** `docs/SYSTEM_PROFILE.md` (X11 details)
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md` (Text pasting options)

---

**Story Status:** Ready for Implementation  
**Prerequisites:** Story 1 + Story 2 complete  
**Blocks:** Story 4 (wrapper script needs toggle mode)  
**Review Required:** PM approval + manual testing validation before Story 4

