# ⚙️ Dictation Module Configuration Options

**Your Preferences:**
- Hotkey: `Ctrl + '` (apostrophe)
- Model: `base.en` (switch to `tiny.en` if speed is an issue)
- System: Manjaro Linux + XFCE + X11

---

## 📁 Configuration File Location

`modules/dictation/config/dictation.env`

This file controls all customizable behavior of the dictation module.

---

## 🎛️ Available Configuration Options

### 1. **Whisper Engine Selection**

```bash
# Choose which whisper implementation to use
WHISPER_ENGINE="faster-whisper"
# Options: "faster-whisper" | "whisper.cpp" | "openai-whisper"
```

**Comparison:**

| Engine | Speed | Setup Complexity | Memory | Recommendation |
|--------|-------|------------------|--------|----------------|
| faster-whisper | Fast (4x RT) | Easy (pip) | Low | ✅ **Recommended** |
| whisper.cpp | Fast (4x RT) | Hard (compile) | Very Low | Advanced users |
| openai-whisper | Slow (1x RT) | Easy (pip) | High | Not recommended |

---

### 2. **Whisper Model Selection**

```bash
# Model for faster-whisper
WHISPER_MODEL="base.en"
# Options: "tiny.en" | "base.en" | "small.en" | "medium.en" | "large-v3"
```

**Model Comparison (Your System - Expected Performance):**

| Model | Speed | Size | Accuracy | Memory | Use Case |
|-------|-------|------|----------|--------|----------|
| **tiny.en** | 8x RT (~1s for 10s) | 75 MB | 85% | ~400 MB | Quick notes, commands |
| **base.en** | 4x RT (~2.5s for 10s) | 145 MB | 95% | ~600 MB | ✅ **Your choice - balanced** |
| **small.en** | 2x RT (~5s for 10s) | 466 MB | 98% | ~1.2 GB | Important documents |
| **medium.en** | 1x RT (~10s for 10s) | 1.5 GB | 99% | ~2.5 GB | Professional transcription |
| **large-v3** | 0.5x RT (~20s for 10s) | 3 GB | 99.5% | ~5 GB | Maximum accuracy |

**RT = Realtime factor (lower is faster)**

**Your Plan:**
```bash
WHISPER_MODEL="base.en"  # Start here
# If too slow, change to:
# WHISPER_MODEL="tiny.en"
```

---

### 3. **Compute Settings (Performance Tuning)**

```bash
# Device to run inference on
WHISPER_DEVICE="cpu"
# Options: "cpu" | "cuda" (if you have NVIDIA GPU)

# Computation precision (affects speed vs accuracy)
WHISPER_COMPUTE_TYPE="int8"
# Options: "int8" | "int16" | "float16" | "float32"
```

**Compute Type Comparison:**

| Type | Speed | Accuracy | Memory | Notes |
|------|-------|----------|--------|-------|
| **int8** | Fastest | 99% of float32 | Lowest | ✅ **Recommended for CPU** |
| int16 | Fast | 99.5% of float32 | Low | Good balance |
| float16 | Medium | 99.9% of float32 | Medium | Requires GPU |
| float32 | Slowest | 100% (baseline) | Highest | Maximum quality |

**Recommended for your system:**
```bash
WHISPER_DEVICE="cpu"
WHISPER_COMPUTE_TYPE="int8"
```

---

### 4. **Audio Input Settings**

```bash
# Sample rate (Hz) - 16000 is optimal for Whisper
SAMPLE_RATE=16000
# Don't change unless you have a specific reason

# Number of audio channels
CHANNELS=1
# Options: 1 (mono, recommended) | 2 (stereo)

# Audio input device
AUDIO_DEVICE=""
# Options:
#   "" (empty) = Use system default
#   "2" = Specific device index (your Blue Microphones is likely device 2)
#   "Blue Microphones" = Device name (partial match)
```

**Finding Your Audio Device:**
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

**Output example:**
```
  0 HD-Audio Generic: ALC1220 Analog (hw:1,0), ALSA (2 in, 8 out)
  1 HD-Audio Generic: ALC1220 Alt Analog (hw:1,2), ALSA (2 in, 0 out)
  2 Blue Microphones: USB Audio (hw:2,0), ALSA (1 in, 0 out)  ← Your mic
```

**Your configuration:**
```bash
# Leave empty to use system default (usually correct)
AUDIO_DEVICE=""

# Or specify if you have multiple mics:
# AUDIO_DEVICE="2"  # Blue Microphones
```

---

### 5. **Audio Quality Settings**

```bash
# Input gain/volume (0.0 to 2.0)
AUDIO_GAIN=1.0
# 1.0 = normal, >1.0 = amplify, <1.0 = reduce

# Noise gate threshold (0.0 to 1.0)
# Audio below this level is considered silence
NOISE_GATE_THRESHOLD=0.01
# Options: 0.0 (no gate) to 1.0 (max gate)
# Useful for reducing background noise

# Minimum recording duration (seconds)
MIN_RECORDING_DURATION=0.5
# Prevents accidental short recordings

# Maximum recording duration (seconds)
MAX_RECORDING_DURATION=300
# Safety limit (5 minutes default)
```

---

### 6. **Text Pasting Behavior**

```bash
# Method for pasting text
PASTE_METHOD="xdotool"
# Options:
#   "xdotool" - Direct typing (X11, your system)
#   "clipboard" - Copy to clipboard, then paste
#   "both" - Type AND copy to clipboard

# Typing speed (milliseconds between keypresses)
TYPING_DELAY=12
# Options: 0-100 (default: 12)
# Lower = faster but might miss keys on slow apps
# Higher = slower but more reliable

# Clear modifiers before typing (prevents stuck keys)
CLEAR_MODIFIERS=true
# Options: true | false
```

**Paste Method Comparison:**

| Method | Speed | Reliability | Clipboard Impact |
|--------|-------|-------------|------------------|
| **xdotool** | Fast | High (X11) | No change | ✅ **Recommended**
| clipboard | Medium | Very High | Overwrites clipboard |
| both | Medium | Very High | Overwrites clipboard |

**Your configuration:**
```bash
PASTE_METHOD="xdotool"
TYPING_DELAY=12
CLEAR_MODIFIERS=true
```

---

### 7. **Text Processing Options**

```bash
# Post-processing filters
STRIP_LEADING_SPACE=true
# Remove space at start of transcription

STRIP_TRAILING_SPACE=true
# Remove space at end of transcription

AUTO_CAPITALIZE=false
# Capitalize first letter (useful for sentences)

AUTO_PUNCTUATION=true
# Keep Whisper's punctuation (. , ? !)

# Replace patterns (comma-separated)
# Format: "pattern1:replacement1,pattern2:replacement2"
TEXT_REPLACEMENTS=""
# Example: "umm:,uh:,you know:" (removes filler words)
```

---

### 8. **Notification Settings**

```bash
# Enable desktop notifications
ENABLE_NOTIFICATIONS=true
# Options: true | false

# Notification tool
NOTIFICATION_TOOL="notify-send"
# Options: "notify-send" | "dunstify" | "none"

# Notification urgency
NOTIFICATION_URGENCY="normal"
# Options: "low" | "normal" | "critical"

# Notification timeout (milliseconds, 0 = default)
NOTIFICATION_TIMEOUT=3000
# 3000 = 3 seconds

# Show transcription in notification
SHOW_TRANSCRIPTION_IN_NOTIFICATION=true
# Options: true | false
# If true, shows the transcribed text in the notification
```

**Your system has:** `notify-send` ✅

---

### 9. **File Management**

```bash
# Temporary directory for audio files
TEMP_DIR="/tmp/dictation"
# Will be created if it doesn't exist

# Keep temporary audio files (for debugging)
KEEP_TEMP_FILES=false
# Options: true | false

# Lock file location
LOCK_FILE="/tmp/dictation.lock"
# Used for state management (recording/not recording)

# Log file location
LOG_FILE="$HOME/.local/share/dictation/dictation.log"
# Set to "" to disable logging
LOG_LEVEL="INFO"
# Options: "DEBUG" | "INFO" | "WARNING" | "ERROR"
```

---

### 10. **Advanced Settings**

```bash
# Whisper language hint
WHISPER_LANGUAGE="en"
# Options: "en" | "es" | "fr" | "de" | etc.
# Helps with accuracy for specific languages

# Whisper VAD (Voice Activity Detection) filter
WHISPER_VAD_FILTER=true
# Options: true | false
# Removes silence before/after speech

# Initial prompt (helps with context/style)
WHISPER_INITIAL_PROMPT=""
# Example: "Technical documentation about Linux systems."
# Helps Whisper understand context

# Beam size (affects accuracy vs speed)
WHISPER_BEAM_SIZE=5
# Options: 1-10 (default: 5)
# Higher = more accurate but slower
# Lower = faster but less accurate

# Temperature (randomness in generation)
WHISPER_TEMPERATURE=0.0
# Options: 0.0-1.0 (default: 0.0)
# 0.0 = deterministic (recommended)
# Higher = more random/creative
```

---

### 11. **Hotkey Configuration**

**Note:** Hotkey is configured in XFCE settings, not in dictation.env

**Your preference: `Ctrl + '` (apostrophe)**

**XFCE GUI Setup:**
1. Settings → Keyboard → Application Shortcuts
2. Add → Command: `/path/to/dictation-toggle.sh`
3. Press `Ctrl + '` when prompted

**XFCE CLI Setup:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
  -p "/commands/custom/<Primary>apostrophe" \
  -n -t string \
  -s "$HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictation-toggle.sh"
```

**Note:** `<Primary>` = Ctrl in XFCE notation

---

## 📝 Example Configuration File

Here's a complete example `config/dictation.env` with your preferences:

```bash
#!/bin/bash
# Dictation Module Configuration
# Customized for: Sidhant's Manjaro + XFCE setup
# Last updated: 2025-10-26

# === WHISPER ENGINE ===
WHISPER_ENGINE="faster-whisper"
WHISPER_MODEL="base.en"              # Start with balanced model
WHISPER_DEVICE="cpu"
WHISPER_COMPUTE_TYPE="int8"          # Optimized for CPU

# === AUDIO INPUT ===
SAMPLE_RATE=16000
CHANNELS=1
AUDIO_DEVICE=""                      # Use system default (Blue Microphones)
AUDIO_GAIN=1.0
MIN_RECORDING_DURATION=0.5
MAX_RECORDING_DURATION=300

# === TEXT PASTING ===
PASTE_METHOD="xdotool"               # X11 system
TYPING_DELAY=12
CLEAR_MODIFIERS=true

# === TEXT PROCESSING ===
STRIP_LEADING_SPACE=true
STRIP_TRAILING_SPACE=true
AUTO_CAPITALIZE=false
AUTO_PUNCTUATION=true
TEXT_REPLACEMENTS=""

# === NOTIFICATIONS ===
ENABLE_NOTIFICATIONS=true
NOTIFICATION_TOOL="notify-send"
NOTIFICATION_URGENCY="normal"
NOTIFICATION_TIMEOUT=3000
SHOW_TRANSCRIPTION_IN_NOTIFICATION=true

# === FILE MANAGEMENT ===
TEMP_DIR="/tmp/dictation"
KEEP_TEMP_FILES=false
LOCK_FILE="/tmp/dictation.lock"
LOG_FILE="$HOME/.local/share/dictation/dictation.log"
LOG_LEVEL="INFO"

# === ADVANCED WHISPER SETTINGS ===
WHISPER_LANGUAGE="en"
WHISPER_VAD_FILTER=true
WHISPER_INITIAL_PROMPT=""
WHISPER_BEAM_SIZE=5
WHISPER_TEMPERATURE=0.0

# === PERFORMANCE TUNING ===
# If base.en is too slow, uncomment this:
# WHISPER_MODEL="tiny.en"
```

---

## 🔄 Switching Models (Your Use Case)

### To switch from base.en to tiny.en:

**Method 1: Edit config file**
```bash
nano modules/dictation/config/dictation.env

# Change this line:
WHISPER_MODEL="base.en"
# To:
WHISPER_MODEL="tiny.en"

# Save and exit
```

**Method 2: Environment variable override**
```bash
# One-time test
WHISPER_MODEL="tiny.en" ./dictation-toggle.sh

# Or export for current session
export WHISPER_MODEL="tiny.en"
./dictation-toggle.sh
```

**Method 3: Setup script helper** (we'll include this)
```bash
./setup.sh --set-model tiny.en
```

---

## 📊 Performance Comparison (Your System)

Based on your Manjaro + CPU setup:

### base.en (Your Starting Choice)
```
Model Load: ~1.5s (first time only)
Transcription: ~2.5s for 10s of speech
Total Latency: ~4s
Accuracy: 95%+
Memory: ~600MB

✅ Good for: General dictation, emails, notes
⚠️ Consider tiny.en if: You want sub-2s response
```

### tiny.en (Fallback if Needed)
```
Model Load: ~0.8s (first time only)
Transcription: ~1.2s for 10s of speech
Total Latency: ~2s
Accuracy: 85-90%
Memory: ~400MB

✅ Good for: Quick commands, short notes
⚠️ Might struggle with: Technical terms, accents
```

---

## 🧪 Testing Different Configurations

**Quick test script:**
```bash
# Test base.en
WHISPER_MODEL="base.en" ./dictation-toggle.sh

# Test tiny.en
WHISPER_MODEL="tiny.en" ./dictation-toggle.sh

# Test with debug logging
LOG_LEVEL="DEBUG" ./dictation-toggle.sh

# Test clipboard method
PASTE_METHOD="clipboard" ./dictation-toggle.sh
```

---

## 🎯 Recommended Starting Configuration

For your first run, we'll use these defaults:

```bash
✅ WHISPER_MODEL="base.en"           # Balanced
✅ WHISPER_COMPUTE_TYPE="int8"       # Optimized for CPU
✅ PASTE_METHOD="xdotool"            # X11
✅ ENABLE_NOTIFICATIONS=true         # Visual feedback
✅ WHISPER_VAD_FILTER=true          # Remove silence
✅ AUDIO_DEVICE=""                   # Auto-detect Blue Mic
```

**Hotkey:** `Ctrl + '` (configured in XFCE)

---

## 📚 Configuration Profiles

You can create multiple config files for different use cases:

```bash
# modules/dictation/config/
├── dictation.env           # Default config
├── dictation-fast.env      # Optimized for speed (tiny.en)
├── dictation-accurate.env  # Optimized for accuracy (small.en)
└── dictation-debug.env     # Debug logging enabled
```

**Use a specific profile:**
```bash
CONFIG_FILE="config/dictation-fast.env" ./dictation-toggle.sh
```

---

## 🔍 Finding the Right Settings

### If transcription is too slow:
1. Try `WHISPER_MODEL="tiny.en"`
2. Reduce `WHISPER_BEAM_SIZE=3`
3. Disable `WHISPER_VAD_FILTER=false`

### If accuracy is poor:
1. Try `WHISPER_MODEL="small.en"`
2. Increase `WHISPER_BEAM_SIZE=7`
3. Add `WHISPER_INITIAL_PROMPT` with context
4. Check microphone placement/quality

### If text pasting is unreliable:
1. Increase `TYPING_DELAY=20`
2. Try `PASTE_METHOD="clipboard"`
3. Check `CLEAR_MODIFIERS=true`

### If background noise is an issue:
1. Adjust `NOISE_GATE_THRESHOLD=0.05`
2. Enable `WHISPER_VAD_FILTER=true`
3. Consider using `AUDIO_GAIN=1.2`

---

## 📖 Next Steps

1. Review this configuration guide
2. Run setup checklist to install dependencies
3. Setup script will create default config with your preferences
4. Test with base.en
5. Switch to tiny.en if needed
6. Fine-tune settings based on your usage

---

**Configuration Guide Version:** 1.0  
**Last Updated:** October 26, 2025  
**Your Preferences:** Ctrl+' hotkey, base.en model (with tiny.en fallback)

