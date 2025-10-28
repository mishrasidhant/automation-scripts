# CRITICAL BUG: Dictation Recording Process Hangs on SIGTERM

**Bug ID:** DICT-BUG-001  
**Severity:** CRITICAL  
**Priority:** HIGH  
**Status:** Confirmed  
**Discovered:** 2025-10-28 (During Story 9 testing)  
**Affects:** All dictation functionality  
**Blocks:** User workflows, Story 9 validation

---

## Summary

The dictation recording process fails to stop gracefully when receiving SIGTERM signal. The signal handler executes but hangs during audio stream cleanup or file saving, causing a 5-second timeout followed by SIGKILL. This results in "Failed to stop recording" errors and prevents successful transcription/text pasting.

---

## Impact

**Severity: CRITICAL** - Core dictation functionality is completely unusable.

- ❌ Recording cannot be stopped successfully
- ❌ Audio files not saved properly
- ❌ Transcription never happens
- ❌ Text never pastes to cursor
- ❌ User experience: Press Ctrl+' → record → press again → error notification
- ✅ Hotkey registration works correctly (Story 9 success)
- ✅ Recording starts successfully

**User-Facing Error:**
```
Notification: "❌ Dictation Error: Failed to stop recording"
```

---

## Reproduction Steps

### Minimal Reproduction

```bash
cd /path/to/automation-scripts

# Method 1: Toggle command (user workflow)
uv run -m automation_scripts.dictation --toggle
# Speak for 2-3 seconds
uv run -m automation_scripts.dictation --toggle
# ERROR: "Failed to stop recording"

# Method 2: Start/stop commands
uv run -m automation_scripts.dictation --start
sleep 3
uv run -m automation_scripts.dictation --stop
# ERROR: Process hangs and gets SIGKILL after 5s
```

### Expected Behavior

1. Recording starts (PID saved to `/tmp/dictation.lock`)
2. User triggers stop command
3. SIGTERM sent to recording process
4. Signal handler saves audio file
5. Lock file removed
6. Process exits with code 0
7. Audio transcribed and text pasted

### Actual Behavior

1. Recording starts (PID saved to `/tmp/dictation.lock`)
2. User triggers stop command
3. SIGTERM sent to recording process ✅
4. Signal handler runs: "Recording interrupted by signal" ✅
5. **Process hangs** (likely during `stream.stop()` or `_save_audio_data()`)
6. After 5 seconds: SIGKILL sent
7. Lock file removed
8. Process exits with code 1 ❌
9. Error notification shown to user

---

## Technical Details

### Affected Code

**File:** `src/automation_scripts/dictation/dictate.py`

**Signal Handler (Lines 720-740):**
```python
def _signal_handler(self, signum, frame):
    """Handle termination signals by saving audio and exiting."""
    print("\n\nRecording interrupted by signal")  # ✅ THIS EXECUTES
    self.recording = False
    
    # Stop the audio stream
    if self.stream and self.stream.active:
        self.stream.stop()    # ❌ LIKELY HANGS HERE
        self.stream.close()
    
    # Save audio data
    if self._save_audio_data():  # ❌ OR HANGS HERE
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        sys.exit(0)
    else:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        sys.exit(1)
```

**Stop Recording Method (Lines 633-667):**
```python
# Send SIGTERM to the recording process
os.kill(recording_pid, signal.SIGTERM)

# Wait for the process to finish (up to 5 seconds)
for i in range(50):
    if not self._is_process_running(recording_pid):
        print("Recording stopped successfully")
        return 0
    time.sleep(0.1)

# If still running after 5 seconds, force kill
if self._is_process_running(recording_pid):
    print("Process did not respond to SIGTERM, sending SIGKILL...", file=sys.stderr)
    os.kill(recording_pid, signal.SIGKILL)  # ❌ THIS HAPPENS
    time.sleep(0.5)
    
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    
    return 1  # ❌ ERROR CODE
```

### Evidence from Logs

```bash
# Console output from test:
🎙️  Recording started (PID: 42519)
Device: default
Audio file: /tmp/dictation/recording-42519-1761669989.wav
Lock file: /tmp/dictation.lock

Press Ctrl+C or run 'dictate.py --stop' to end recording
Stopping...
Stopping recording process (PID: 42519)...

Recording interrupted by signal  # ✅ Signal handler started
Process did not respond to SIGTERM, sending SIGKILL...  # ❌ Timeout after 5s
```

### Suspected Root Cause

1. **Audio Stream Cleanup:** `sounddevice` stream may hang during `stream.stop()` or `stream.close()`
2. **File I/O Blocking:** `_save_audio_data()` may block on file write operations
3. **NumPy Array Concatenation:** Large audio buffers may cause memory/processing hang
4. **PortAudio Backend Issue:** Underlying audio library may not release resources cleanly

---

## Environment

**Tested On:**
- OS: Manjaro Linux 6.6.107-1-MANJARO
- Desktop: XFCE + X11
- Python: 3.11+
- UV: Latest
- Audio Backend: PortAudio (sounddevice)

**System Audio:**
- Default device: Working (recording starts successfully)
- Audio capture: Functional

---

## Temporary Workarounds

### For Users

**None Available** - Dictation functionality is currently broken.

Users can verify hotkey registration works:
```bash
# Check service (Story 9 verification)
systemctl --user status dictation-hotkey.service

# Verify hotkey registered
xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe"
```

### For Developers

**Manual Cleanup:**
```bash
# Kill stuck processes
pkill -9 -f "automation_scripts.dictation"

# Remove lock file
rm -f /tmp/dictation.lock
```

---

## Proposed Investigation Steps

### Priority 1: Isolate Hang Location

Add debug logging to pinpoint exact hang location:

```python
def _signal_handler(self, signum, frame):
    print("Signal handler: START")
    self.recording = False
    
    print("Signal handler: Stopping stream...")
    if self.stream and self.stream.active:
        print("Signal handler: Calling stream.stop()...")
        self.stream.stop()  # Add timeout here?
        print("Signal handler: Stream stopped")
        
        print("Signal handler: Calling stream.close()...")
        self.stream.close()
        print("Signal handler: Stream closed")
    
    print("Signal handler: Saving audio data...")
    if self._save_audio_data():
        print("Signal handler: Audio saved successfully")
        # ... cleanup
```

### Priority 2: Test Audio Stream Behavior

```python
# Test if sounddevice stream can be stopped from signal handler
import sounddevice as sd
import signal
import sys

stream = sd.InputStream(callback=lambda *args: None)
stream.start()

def handler(sig, frame):
    print("Stopping stream...")
    stream.stop()  # Does this hang?
    print("Stream stopped")
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)
# Send SIGTERM and observe behavior
```

### Priority 3: Review Audio Buffer Management

Check if large audio buffers cause issues:
- Current buffer size
- Memory usage during recording
- NumPy concatenation performance

---

## Recommended Fix Strategy

### Option 1: Graceful Stream Shutdown (Preferred)

```python
def _signal_handler(self, signum, frame):
    print("\n\nRecording interrupted by signal")
    self.recording = False
    
    # Stop stream with timeout protection
    if self.stream and self.stream.active:
        try:
            # Use threading to timeout stream.stop()
            import threading
            
            def stop_stream():
                self.stream.stop()
                self.stream.close()
            
            thread = threading.Thread(target=stop_stream)
            thread.daemon = True
            thread.start()
            thread.join(timeout=2.0)  # 2 second timeout
            
            if thread.is_alive():
                print("Warning: Stream did not stop cleanly", file=sys.stderr)
                # Force exit anyway
                
        except Exception as e:
            print(f"Error stopping stream: {e}", file=sys.stderr)
    
    # Save audio data (also with timeout protection)
    # ... rest of handler
```

### Option 2: Async Signal Handling

Use a flag-based approach instead of direct cleanup in signal handler:

```python
def _signal_handler(self, signum, frame):
    """Set flag to stop recording in main loop."""
    self.recording = False
    self.stop_requested = True  # Main loop will handle cleanup

def start_recording(self):
    # ... setup ...
    
    while self.recording:
        # Recording loop
        time.sleep(0.1)
        
        if self.stop_requested:
            # Clean up in main thread context (safer)
            self.stream.stop()
            self.stream.close()
            self._save_audio_data()
            break
```

### Option 3: Separate Stop Process

Don't rely on signal handling for stop - use IPC:

```python
# Use a control file instead of SIGTERM
STOP_REQUEST_FILE = Path("/tmp/dictation.stop")

def start_recording(self):
    while self.recording:
        if STOP_REQUEST_FILE.exists():
            STOP_REQUEST_FILE.unlink()
            break  # Clean stop in main loop
        time.sleep(0.1)
    
    # Clean up normally (not in signal handler)
    self.stream.stop()
    self.stream.close()
    self._save_audio_data()
```

---

## Testing Checklist

Once fix is implemented:

- [ ] Test toggle command: Start → Stop → Transcribe → Paste
- [ ] Test with short recordings (1-2 seconds)
- [ ] Test with long recordings (30+ seconds)
- [ ] Test with no speech detected
- [ ] Test with background noise
- [ ] Test rapid start/stop cycles
- [ ] Test SIGTERM handling directly
- [ ] Test SIGINT handling (Ctrl+C)
- [ ] Verify no audio files left in `/tmp/dictation/`
- [ ] Verify no stale lock files
- [ ] Verify no zombie processes
- [ ] Test on different audio devices
- [ ] Test with Story 9 hotkey integration

---

## Related Issues

- **Story 9:** Systemd Service & Hotkey Persistence (✅ Complete - hotkey works)
- **Story 8:** UV Migration (✅ Complete - package structure works)
- **This Bug:** Blocks actual dictation usage

---

## Next Steps

1. **Assign Priority:** HIGH (blocks core functionality)
2. **Assign Owner:** TBD
3. **Create Story:** "Fix dictation SIGTERM hang during audio stream cleanup"
4. **Estimate:** 2-4 hours (investigation + fix + testing)
5. **Target:** Immediate (next sprint)

---

## Notes

**Discovered By:** James (AI Dev Agent) during Story 9 manual testing  
**Date:** 2025-10-28  
**Context:** Story 9 hotkey persistence works perfectly - this is a separate dictation module bug  
**Scope:** Pre-existing bug, not introduced by Story 9 changes

**Important:** This bug does NOT invalidate Story 9. The hotkey registration and persistence across reboots works correctly. The issue is in the core dictation module's recording/stopping logic.

---

**Last Updated:** 2025-10-28  
**Status:** Awaiting fix assignment

