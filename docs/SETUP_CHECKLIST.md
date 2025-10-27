# ✅ System Setup Checklist

**System:** Manjaro Linux + XFCE + X11  
**Purpose:** Pre-flight checklist before implementing dictation module  
**Date:** October 26, 2025

---

## Prerequisites Checklist

### System Packages

Run these commands to install missing dependencies:

```bash
# Required packages for dictation module
sudo pacman -S --needed xdotool portaudio libnotify

# Verification
which xdotool     # Should output: /usr/bin/xdotool
which notify-send # Should output: /usr/bin/notify-send
```

**Status:**
- [ ] xdotool installed
- [ ] portaudio installed
- [ ] libnotify installed

---

### Python Packages

```bash
# Install required Python libraries
pip install --user sounddevice faster-whisper

# Verification
python3 -c "import sounddevice; print('sounddevice:', sounddevice.__version__)"
python3 -c "import faster_whisper; print('faster-whisper installed')"
python3 -c "import numpy; print('numpy:', numpy.__version__)"
```

**Status:**
- [x] numpy installed (2.3.3) ✓
- [ ] sounddevice installed
- [ ] faster-whisper installed

---

## System Validation

### 1. Audio Input Test

```bash
# List available audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Expected output should include:
# - Blue Microphones USB Audio (recommended)
# - HD-Audio Generic (fallback)

# Test recording (5 seconds)
python3 -c "
import sounddevice as sd
import numpy as np
print('Recording 5 seconds...')
audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='int16')
sd.wait()
print('Recording complete!')
print(f'Captured {len(audio)} samples')
"
```

**Status:**
- [ ] Audio devices detected
- [ ] Blue Microphones USB found
- [ ] Test recording successful

---

### 2. Whisper Model Test

```bash
# Test faster-whisper installation and model download
python3 << 'EOF'
from faster_whisper import WhisperModel
import tempfile
import numpy as np
import wave

# Create a dummy audio file (1 second of silence)
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    filename = f.name
    with wave.open(filename, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00' * 16000 * 2)

print("Loading model (first run downloads model)...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("Model loaded successfully!")

# Test transcription
segments, info = model.transcribe(filename)
print(f"Transcription test complete!")
print(f"Language: {info.language}, probability: {info.language_probability:.2f}")

import os
os.unlink(filename)
print("✓ Whisper test passed!")
EOF
```

**Status:**
- [ ] Model download successful
- [ ] Model loading works
- [ ] Transcription test passed

---

### 3. Text Injection Test

```bash
# Test xdotool (will type text in active window after 3s delay)
echo "Switching to a text editor in 3 seconds..."
sleep 3
xdotool type "Hello from xdotool!"
```

**Alternative test (doesn't require window focus):**
```bash
# Test xdotool command works
xdotool getactivewindow getwindowname
# Should output your current window title
```

**Status:**
- [ ] xdotool installed and working
- [ ] Text injection test successful

---

### 4. Notification Test

```bash
# Test notification system
notify-send "Test Notification" "If you see this, notifications are working!"

# Test with different urgency levels
notify-send -u critical "Dictation" "Recording started..."
notify-send -u normal "Dictation" "Transcribing..."
notify-send -u low "Dictation" "Complete!"
```

**Status:**
- [ ] Notifications appearing
- [ ] Icons displaying correctly

---

### 5. XFCE Shortcuts Test

```bash
# Verify XFCE keyboard shortcuts are accessible
xfconf-query -c xfce4-keyboard-shortcuts -l | grep custom | head -5

# Expected: List of existing custom shortcuts
```

**Status:**
- [ ] xfconf-query accessible
- [ ] Custom shortcuts visible

---

## Performance Baseline

Run this benchmark to establish expected performance:

```bash
# Create benchmark script
python3 << 'EOF'
import time
import tempfile
import wave
import numpy as np
from faster_whisper import WhisperModel

# Generate 10 seconds of random audio (simulating speech)
duration = 10
sample_rate = 16000
audio_data = np.random.randint(-5000, 5000, duration * sample_rate, dtype=np.int16)

# Save to WAV
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    filename = f.name
    with wave.open(filename, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_data.tobytes())

# Benchmark
print("Loading model...")
start = time.time()
model = WhisperModel("base.en", device="cpu", compute_type="int8")
load_time = time.time() - start
print(f"Model load time: {load_time:.2f}s")

print("Transcribing 10s of audio...")
start = time.time()
segments, info = model.transcribe(filename)
list(segments)  # Force processing
transcribe_time = time.time() - start
print(f"Transcription time: {transcribe_time:.2f}s")
print(f"Real-time factor: {transcribe_time / duration:.2f}x")

import os
os.unlink(filename)

print("\n✓ Benchmark complete!")
print(f"Expected total latency for 10s speech: ~{load_time + transcribe_time:.1f}s")
EOF
```

**Expected Results (Your System):**
- Model load time: ~1.0-2.0s (first run only)
- Transcription time: ~2.5s for 10s audio
- Real-time factor: ~0.25x (4x realtime)

**Status:**
- [ ] Benchmark completed
- [ ] Performance acceptable

---

## Module Directory Structure

Before implementation, create the module structure:

```bash
cd $HOME/Files/W/Workspace/git/automation/automation-scripts

# Create module directory
mkdir -p modules/dictation/config

# Move staging script
# (This will be done during implementation phase)

# Expected structure:
tree modules/dictation/
# modules/dictation/
# ├── README.md
# ├── dictate.py
# ├── dictation-toggle.sh
# ├── setup.sh
# └── config/
#     └── dictation.env
```

**Status:**
- [ ] Directory structure created
- [ ] Staging script reviewed

---

## Environment Variables

Test that the system can access required environment variables:

```bash
# Verify display
echo "DISPLAY: $DISPLAY"
# Expected: :0 or :1

# Verify X authority
echo "XAUTHORITY: $XAUTHORITY"
# Expected: $HOME/.Xauthority

# Verify desktop session
echo "XDG_SESSION_TYPE: $XDG_SESSION_TYPE"
# Expected: x11

# Verify current desktop
echo "XDG_CURRENT_DESKTOP: $XDG_CURRENT_DESKTOP"
# Expected: XFCE
```

**Status:**
- [ ] DISPLAY set correctly
- [ ] XAUTHORITY accessible
- [ ] Session type is X11
- [ ] Desktop is XFCE

---

## Final Verification

### Complete System Check

```bash
# Run comprehensive check
cat << 'EOF' | bash
#!/bin/bash
echo "=== System Readiness Check ==="
echo ""

# Check each requirement
checks=0
passed=0

# System packages
for cmd in xdotool notify-send python3; do
    checks=$((checks + 1))
    if command -v $cmd &> /dev/null; then
        echo "✓ $cmd installed"
        passed=$((passed + 1))
    else
        echo "✗ $cmd NOT FOUND"
    fi
done

# Python packages
for pkg in sounddevice faster_whisper numpy; do
    checks=$((checks + 1))
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "✓ Python package: $pkg"
        passed=$((passed + 1))
    else
        echo "✗ Python package: $pkg NOT INSTALLED"
    fi
done

# Environment
checks=$((checks + 1))
if [ "$XDG_SESSION_TYPE" = "x11" ]; then
    echo "✓ Display server: X11"
    passed=$((passed + 1))
else
    echo "✗ Display server: $XDG_SESSION_TYPE (expected x11)"
fi

checks=$((checks + 1))
if [ "$XDG_CURRENT_DESKTOP" = "XFCE" ]; then
    echo "✓ Desktop: XFCE"
    passed=$((passed + 1))
else
    echo "✗ Desktop: $XDG_CURRENT_DESKTOP (expected XFCE)"
fi

echo ""
echo "=== Results: $passed/$checks checks passed ==="

if [ $passed -eq $checks ]; then
    echo "✓ System is READY for dictation module implementation!"
    exit 0
else
    echo "⚠ Please install missing dependencies"
    exit 1
fi
EOF
```

---

## Installation Commands (If Needed)

If any checks fail, run the appropriate commands:

### Missing System Packages
```bash
sudo pacman -S --needed xdotool portaudio libnotify python-pip
```

### Missing Python Packages
```bash
pip install --user sounddevice faster-whisper
```

### Path Issues
```bash
# Ensure pip packages are in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Next Steps

Once all checkboxes are complete:

1. ✅ Run the "Final Verification" script
2. ✅ Ensure all tests pass
3. ✅ Document any system-specific notes below
4. ➡️ **Proceed to implementation phase**

---

## System-Specific Notes

(Add any custom configuration or issues encountered here)

```
# Example:
- Blue Microphones detected as device index 2
- PulseAudio latency: default (good for speech)
- XFCE version: 4.18
- Python user packages location: $HOME/.local/lib/python3.13/site-packages
```

---

**Checklist Version:** 1.0  
**Last Updated:** October 26, 2025  
**System Validated By:** (Fill in after completion)

