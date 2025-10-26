# Story 1: Core Dictation Script - Audio Recording

**Story ID:** DICT-001  
**Epic:** Dictation Module Implementation  
**Priority:** High (Foundation)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 hours

---

## User Story

**As a** user who wants to dictate text,  
**I want** the system to record audio from my microphone when triggered,  
**So that** I can capture my speech for transcription.

---

## Story Context

### Existing System Integration

- **Integrates with:** New module (no existing dictation functionality)
- **Technology:** Python 3.13.7, sounddevice library, PulseAudio
- **Audio Hardware:** Blue Microphones USB Audio (Card 2)
- **Follows pattern:** Command-line Python scripts in systemd-automations

### Technical Approach

Implement the foundational audio recording capability using:
- `sounddevice` library for Python-native audio capture
- PulseAudio for audio system integration
- WAV format for compatibility with speech recognition
- Command-line arguments (`--start`, `--stop`) for control

---

## Acceptance Criteria

### Functional Requirements

1. **Script accepts CLI arguments for recording control**
   - `python3 dictate.py --start` begins recording
   - `python3 dictate.py --stop` ends recording
   - Invalid arguments show usage help

2. **Audio recording captures from default microphone**
   - Uses system default audio input (Blue Microphones)
   - Records at 16kHz sample rate (optimal for Whisper)
   - Records mono audio (1 channel)
   - Saves to WAV format

3. **Audio files are saved to temporary location**
   - Files saved to `/tmp/dictation/` directory
   - Filename includes timestamp/PID for uniqueness
   - Directory created automatically if missing

### Integration Requirements

4. **Script runs without root/sudo privileges**
   - Uses user-level audio device access
   - No elevated permissions required

5. **Dependencies are clearly documented**
   - Import statements include error handling
   - Missing dependencies show helpful error messages

6. **Lock file indicates recording state**
   - `/tmp/dictation.lock` created on `--start`
   - Lock file contains PID and audio file path
   - Lock file removed on `--stop`

### Quality Requirements

7. **Error handling for common audio issues**
   - Detects if no audio input device available
   - Handles audio device busy/in-use errors
   - Provides clear error messages to user

8. **Visual feedback via notifications**
   - Desktop notification on recording start
   - Desktop notification on recording stop
   - Uses `notify-send` for XFCE integration

9. **Audio quality is suitable for transcription**
   - Sample rate: 16000 Hz (Whisper requirement)
   - Bit depth: 16-bit PCM
   - Format: WAV (uncompressed)

---

## Technical Implementation Details

### File Structure

```
modules/dictation/
├── dictate.py          # Core script (this story)
└── config/             # (Created but empty for now)
```

### Key Python Components

```python
# Required imports
import sounddevice as sd
import wave
import json
import os
import subprocess
import argparse
from pathlib import Path
```

### Lock File Format

```json
{
  "pid": 12345,
  "started_at": 1729900000,
  "audio_file": "/tmp/dictation/recording-12345.wav",
  "stream_info": {
    "device": "Blue Microphones",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

### Audio Recording Parameters

- **Sample Rate:** 16000 Hz (Whisper optimized)
- **Channels:** 1 (mono)
- **Bit Depth:** 16-bit signed integer
- **Format:** WAV (PCM)
- **Device:** System default (auto-detected)

---

## Implementation Checklist

### Phase 1: Basic Structure
- [ ] Create `modules/dictation/` directory
- [ ] Create `dictate.py` with argument parsing
- [ ] Implement `--start`, `--stop`, `--help` arguments
- [ ] Add logging setup (optional for debugging)

### Phase 2: Audio Recording
- [ ] Import sounddevice library
- [ ] Query available audio devices
- [ ] Implement audio recording function
- [ ] Save audio to WAV file format
- [ ] Test with actual microphone

### Phase 3: State Management
- [ ] Implement lock file creation (JSON format)
- [ ] Store PID, timestamp, audio file path
- [ ] Check for existing lock on start
- [ ] Clean up lock file on stop

### Phase 4: User Feedback
- [ ] Add notify-send integration
- [ ] Show "Recording started" notification
- [ ] Show "Recording stopped" notification
- [ ] Include recording duration in stop notification

### Phase 5: Error Handling
- [ ] Check for sounddevice library availability
- [ ] Handle missing audio input device
- [ ] Handle audio device busy errors
- [ ] Handle permission errors
- [ ] Handle disk space errors (temp directory)

---

## Testing Strategy

### Unit Tests

```python
# Test lock file creation
def test_lock_file_creation():
    # Start recording, verify lock file exists and is valid JSON
    pass

# Test audio device detection
def test_audio_device_query():
    # Verify sounddevice can list devices
    pass

# Test WAV file creation
def test_wav_file_format():
    # Record 1 second, verify WAV file is valid
    pass
```

### Manual Tests

1. **Basic Recording Test**
   ```bash
   python3 dictate.py --start
   # Speak for 5 seconds
   python3 dictate.py --stop
   # Verify: WAV file exists in /tmp/dictation/
   # Verify: File can be played with aplay
   ```

2. **Multiple Recording Test**
   ```bash
   # Start and stop 3 times
   # Verify: 3 separate WAV files with unique names
   ```

3. **Error Handling Test**
   ```bash
   # Unplug microphone (if USB)
   python3 dictate.py --start
   # Verify: Clear error message, no crash
   ```

4. **Lock File Test**
   ```bash
   python3 dictate.py --start
   python3 dictate.py --start  # Second call while recording
   # Verify: Error message about already recording
   ```

---

## Definition of Done

- ✅ Script can start audio recording via `--start` argument
- ✅ Script can stop audio recording via `--stop` argument
- ✅ Audio is saved to WAV file in `/tmp/dictation/`
- ✅ Lock file tracks recording state correctly
- ✅ Desktop notifications provide user feedback
- ✅ Error handling covers common audio issues
- ✅ No root/sudo required for operation
- ✅ Manual tests pass successfully
- ✅ Code includes inline comments explaining key sections

---

## Dependencies

### System Dependencies
- PulseAudio (already installed ✓)
- libnotify / notify-send (already installed ✓)
- portaudio (needs installation: `sudo pacman -S portaudio`)

### Python Dependencies
- sounddevice (needs installation: `pip install sounddevice`)
- numpy (already installed ✓)

### Installation Commands
```bash
# System dependencies
sudo pacman -S portaudio

# Python dependencies
pip install sounddevice
```

---

## Example Usage (After Implementation)

```bash
# Terminal 1: Start recording
$ python3 modules/dictation/dictate.py --start
🎙️ Recording started... (Press Ctrl+C or use --stop to end)

# Terminal 2: Check lock file
$ cat /tmp/dictation.lock
{"pid": 12345, "started_at": 1729900000, "audio_file": "/tmp/dictation/recording-12345.wav"}

# Terminal 1: Stop recording (after speaking)
$ python3 modules/dictation/dictate.py --stop
✅ Recording stopped. Saved to: /tmp/dictation/recording-12345.wav

# Play back the recording
$ aplay /tmp/dictation/recording-12345.wav
```

---

## Success Metrics

- **Functionality:** Can record and save audio successfully
- **Reliability:** No crashes during 10 consecutive record/stop cycles
- **Latency:** Recording starts within 500ms of command
- **Audio Quality:** WAV file plays back clearly in aplay/audacity
- **User Experience:** Notifications appear within 1 second of action

---

## Technical Notes

### Audio Device Detection

The script should auto-detect the Blue Microphones USB Audio device as the default input. If not:

```bash
# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Set default device (if needed)
# This will be configurable in later stories
```

### Lock File Behavior

- **Location:** `/tmp/dictation.lock` (cleared on reboot)
- **Format:** JSON for easy parsing
- **Purpose:** Prevents multiple simultaneous recordings
- **Cleanup:** Removed on normal stop, orphaned on crash

### Future Integration Points

This story provides the foundation for:
- Story 2: Transcription (reads the WAV file)
- Story 3: Text injection (triggered after recording stops)
- Story 4: Wrapper script (calls this script with arguments)

---

## Risk Assessment

### Risks

1. **Audio device not accessible**
   - **Mitigation:** Clear error message with device listing
   - **Likelihood:** Low (PulseAudio handles permissions)

2. **Lock file corruption**
   - **Mitigation:** Validate JSON on read, recreate if invalid
   - **Likelihood:** Very Low

3. **Disk space exhaustion**
   - **Mitigation:** Check available space before recording
   - **Likelihood:** Low (temp files are small, ~1MB per minute)

### Rollback Plan

If issues arise:
1. Stop any running recording process
2. Remove `/tmp/dictation.lock`
3. Clear `/tmp/dictation/` directory
4. Uninstall sounddevice: `pip uninstall sounddevice`

---

## Related Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md` (Section: Implementation Details)
- **System Profile:** `docs/SYSTEM_PROFILE.md` (Audio System section)
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md` (Audio settings)

---

**Story Status:** Ready for Implementation  
**Prerequisites:** None (foundation story)  
**Blocks:** Story 2 (transcription), Story 3 (text injection)  
**Review Required:** PM approval before starting Story 2

