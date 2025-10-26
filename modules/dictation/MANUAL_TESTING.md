# Manual Testing Guide - Story 1 (DICT-001)

This guide provides step-by-step manual testing procedures for the audio recording functionality.

**⚠️ Important:** Keep the virtual environment activated throughout all tests. All commands assume the venv is active.

## Prerequisites

Before testing, install required dependencies:

```bash
# System dependencies
sudo pacman -S portaudio xdotool libnotify

# Setup Python virtual environment and dependencies
cd $AUTOMATION_SCRIPTS_DIR
source scripts/setup-dev.sh dictation
```

Verify installations:
```bash
# System deps
which notify-send xdotool  # Should show paths
ldconfig -p | grep portaudio  # Should show library

# Python deps (with venv activated)
python -c "import sounddevice; print('sounddevice OK')"
python -c "import numpy; print('numpy OK')"
```

## Test 1: Basic Recording

**Objective:** Verify basic start/stop functionality

```bash
# Ensure venv is activated
cd $AUTOMATION_SCRIPTS_DIR
source .venv/bin/activate

cd modules/dictation

# Start recording
python dictate.py --start

# Expected:
# - "🎙️ Recording started..." message
# - Desktop notification appears
# - Lock file created at /tmp/dictation.lock

# Verify lock file exists
cat /tmp/dictation.lock
# Should show JSON with pid, started_at, audio_file, stream_info

# Speak for 5-10 seconds
# Say something like: "This is a test recording for the dictation module."

# Stop recording (in another terminal or press Ctrl+C)
python3 dictate.py --stop

# Expected:
# - "✅ Recording stopped" message
# - Desktop notification with duration
# - Lock file removed
# - WAV file created in /tmp/dictation/
```

**Verification:**
```bash
# Check file exists
ls -lh /tmp/dictation/

# Play back recording
aplay /tmp/dictation/recording-*.wav

# Verify audio quality - should hear your voice clearly
```

**Pass Criteria:**
- ✅ Recording starts without errors
- ✅ Lock file created and contains valid JSON
- ✅ Desktop notifications appear (both start and stop)
- ✅ Recording stops successfully
- ✅ WAV file created and is playable
- ✅ Audio quality is clear and understandable

---

## Test 2: Audio File Format Validation

**Objective:** Verify WAV file meets Whisper requirements

```bash
# Check WAV file properties
file /tmp/dictation/recording-*.wav

# Expected output should include:
# - WAVE audio
# - Microsoft PCM
# - 16 bit
# - mono
# - 16000 Hz

# More detailed check
python3 -c "
import wave
with wave.open('/tmp/dictation/recording-$(ls /tmp/dictation/ | grep recording | head -1)', 'rb') as wf:
    print(f'Channels: {wf.getnchannels()}')  # Should be 1
    print(f'Sample width: {wf.getsampwidth()}')  # Should be 2 (16-bit)
    print(f'Frame rate: {wf.getframerate()}')  # Should be 16000
"
```

**Pass Criteria:**
- ✅ Channels: 1 (mono)
- ✅ Sample width: 2 bytes (16-bit)
- ✅ Sample rate: 16000 Hz

---

## Test 3: Multiple Recording Sessions

**Objective:** Verify unique filenames and no conflicts

```bash
# Clear previous recordings
rm -f /tmp/dictation/*.wav

# Run 3 separate recording sessions
for i in {1..3}; do
  echo "Recording session $i..."
  python3 dictate.py --start &
  sleep 2
  python3 dictate.py --stop
  sleep 1
done

# Check number of files created
ls -1 /tmp/dictation/*.wav | wc -l
# Should output: 3
```

**Pass Criteria:**
- ✅ 3 separate WAV files created
- ✅ Each file has unique name (PID + timestamp)
- ✅ No files overwritten

---

## Test 4: Lock File Prevents Concurrent Recording

**Objective:** Verify lock file prevents duplicate recordings

```bash
# Start recording
python3 dictate.py --start &
FIRST_PID=$!

# Try to start another recording while first is active
sleep 1
python3 dictate.py --start

# Expected:
# - Error message: "Error: Recording already in progress"
# - Desktop notification: "Recording already in progress"

# Stop the first recording
python3 dictate.py --stop

# Verify only one WAV file created
ls /tmp/dictation/recording-*.wav
```

**Pass Criteria:**
- ✅ Second start attempt fails with clear error
- ✅ Error notification appears
- ✅ Only one recording file created

---

## Test 5: Lock File Cleanup on Crash

**Objective:** Verify stale lock files are handled

```bash
# Start recording
python3 dictate.py --start &
RECORDING_PID=$!

# Force-kill the recording process (simulate crash)
sleep 2
kill -9 $RECORDING_PID

# Lock file will remain (stale)
cat /tmp/dictation.lock
# Shows PID of killed process

# Try to start new recording
python3 dictate.py --start

# Expected:
# - Stale lock detected and removed
# - New recording starts successfully
# - New lock file created with current PID

# Stop recording
sleep 2
python3 dictate.py --stop
```

**Pass Criteria:**
- ✅ Stale lock file detected
- ✅ New recording starts despite stale lock
- ✅ New lock file has current PID

---

## Test 6: Error Handling - No Audio Device

**Objective:** Verify graceful handling of missing audio device

```bash
# This test is difficult without unplugging USB mic
# Instead, test with invalid device configuration

# If using USB microphone, unplug it temporarily
# Then run:
python3 dictate.py --start

# Expected:
# - Clear error message about audio device
# - Desktop notification with error
# - No crash
# - No lock file created

# Plug microphone back in and verify recovery
python3 dictate.py --start
# Should work normally
```

**Pass Criteria:**
- ✅ Clear error message displayed
- ✅ Error notification appears
- ✅ Script exits gracefully (no crash)
- ✅ No lock file created on failure

---

## Test 7: Desktop Notifications

**Objective:** Verify all notifications appear correctly

```bash
# Test start notification
python3 dictate.py --start
# Check notification area for: "🎙️ Dictation - Recording started..."

sleep 3

# Test stop notification
python3 dictate.py --stop
# Check notification area for: "✅ Dictation - Recording stopped (Xs)"
# Should include duration in seconds
```

**Pass Criteria:**
- ✅ Start notification appears with recording icon
- ✅ Stop notification appears with checkmark
- ✅ Stop notification includes duration
- ✅ Notifications visible for appropriate time

---

## Test 8: CLI Arguments and Help

**Objective:** Verify command-line interface

```bash
# Test help
python3 dictate.py --help
# Should display usage information

# Test no arguments
python3 dictate.py
# Should display error and usage

# Test conflicting arguments
python3 dictate.py --start --stop
# Should display error about conflicting arguments
```

**Pass Criteria:**
- ✅ Help text is clear and complete
- ✅ Error messages are helpful
- ✅ Invalid usage shows correct syntax

---

## Test 9: Disk Space and Permissions

**Objective:** Verify file system handling

```bash
# Check /tmp/dictation/ directory creation
rm -rf /tmp/dictation
python3 dictate.py --start
ls -ld /tmp/dictation/
# Should be created automatically

python3 dictate.py --stop

# Verify permissions (should be user-owned)
ls -l /tmp/dictation/*.wav
# Owner should be current user, not root
```

**Pass Criteria:**
- ✅ Directory created automatically if missing
- ✅ Files owned by current user (not root)
- ✅ No sudo/root required

---

## Test 10: Recording Duration Accuracy

**Objective:** Verify timing accuracy

```bash
# Record for exactly 10 seconds
python3 dictate.py --start
sleep 10
python3 dictate.py --stop

# Check reported duration (should be ~10 seconds)
# Check actual file duration
soxi -D /tmp/dictation/recording-*.wav
# or
ffprobe -i /tmp/dictation/recording-*.wav -show_entries format=duration -v quiet -of csv="p=0"

# Duration should be close to 10 seconds (±1 second tolerance)
```

**Pass Criteria:**
- ✅ Reported duration matches actual recording time
- ✅ No significant drift or timing issues

---

## Full Regression Test

Run all tests in sequence:

```bash
# Clean slate
rm -rf /tmp/dictation
rm -f /tmp/dictation.lock

# Run test suite
python3 test_dictate.py

# Run manual tests 1-10 in order
# Document any failures

# Final cleanup
rm -rf /tmp/dictation
rm -f /tmp/dictation.lock
```

---

## Success Metrics (from Story)

- **Functionality:** ✅ Can record and save audio successfully
- **Reliability:** ✅ No crashes during 10 consecutive record/stop cycles
- **Latency:** ✅ Recording starts within 500ms of command
- **Audio Quality:** ✅ WAV file plays back clearly in aplay/audacity
- **User Experience:** ✅ Notifications appear within 1 second of action

---

## Reporting Issues

If any test fails, document:
1. Test number and name
2. Expected behavior
3. Actual behavior
4. Error messages (if any)
5. System state (audio devices, disk space, etc.)

Include output of:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
df -h /tmp
pulseaudio --check && echo "PulseAudio running" || echo "PulseAudio not running"
```

---

## Test Results Template

```
Story 1 (DICT-001) Manual Testing Results
Date: __________
Tester: __________

Test 1 - Basic Recording: [ PASS / FAIL ]
Test 2 - Audio Format: [ PASS / FAIL ]
Test 3 - Multiple Sessions: [ PASS / FAIL ]
Test 4 - Lock File Prevention: [ PASS / FAIL ]
Test 5 - Lock File Cleanup: [ PASS / FAIL ]
Test 6 - Error Handling: [ PASS / FAIL ]
Test 7 - Notifications: [ PASS / FAIL ]
Test 8 - CLI Arguments: [ PASS / FAIL ]
Test 9 - Permissions: [ PASS / FAIL ]
Test 10 - Duration Accuracy: [ PASS / FAIL ]

Overall: [ PASS / FAIL ]

Notes:
__________________________________________
```

