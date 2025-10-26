# 👤 User Preferences

**User:** Sidhant Dixit  
**Date:** October 26, 2025  
**Purpose:** Document user-specific configuration choices for dictation module

---

## ⚙️ Configuration Choices

### Hotkey
```
Hotkey: Ctrl + ' (apostrophe)
XFCE Command Path: <Primary>apostrophe
```

**XFCE Setup Command:**
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
  -p "/commands/custom/<Primary>apostrophe" \
  -n -t string \
  -s "/home/sdx/Files/W/Workspace/git/automation/systemd-automations/modules/dictation/dictation-toggle.sh"
```

### Whisper Model
```
Primary Model: base.en
Fallback Model: tiny.en (if speed is an issue)
```

**Rationale:**
- `base.en` provides good balance (95% accuracy, 4x realtime)
- `tiny.en` available as fallback for faster response (~8x realtime)
- Can switch by editing `config/dictation.env`

### System Configuration
```yaml
OS: Manjaro Linux
Desktop: XFCE
Display: X11
Audio Device: Blue Microphones USB Audio
Python: 3.13.7
```

---

## 📋 Default Configuration File

Your `modules/dictation/config/dictation.env` will be created with:

```bash
#!/bin/bash
# Dictation Configuration - Sidhant's Preferences
# Created: 2025-10-26

# === WHISPER ENGINE ===
WHISPER_ENGINE="faster-whisper"
WHISPER_MODEL="base.en"              # Start here, switch to tiny.en if needed
WHISPER_DEVICE="cpu"
WHISPER_COMPUTE_TYPE="int8"

# === AUDIO INPUT ===
SAMPLE_RATE=16000
CHANNELS=1
AUDIO_DEVICE=""                      # Auto-detect Blue Microphones
AUDIO_GAIN=1.0
MIN_RECORDING_DURATION=0.5
MAX_RECORDING_DURATION=300

# === TEXT PASTING ===
PASTE_METHOD="xdotool"               # X11
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
```

---

## 🔄 How to Switch to tiny.en

If `base.en` feels too slow, switch models:

### Method 1: Edit Configuration File
```bash
nano modules/dictation/config/dictation.env

# Find this line:
WHISPER_MODEL="base.en"

# Change to:
WHISPER_MODEL="tiny.en"

# Save (Ctrl+O) and Exit (Ctrl+X)
```

### Method 2: One-Time Override
```bash
# Test tiny.en without changing config
WHISPER_MODEL="tiny.en" ./dictation-toggle.sh
```

### Method 3: Create Alternative Profile
```bash
# Copy config
cp config/dictation.env config/dictation-fast.env

# Edit the copy
nano config/dictation-fast.env
# Change to: WHISPER_MODEL="tiny.en"

# Use it:
CONFIG_FILE="config/dictation-fast.env" ./dictation-toggle.sh
```

---

## 📊 Expected Performance

### With base.en (Your Default)
```
Initial Model Load: ~1.5s (first run only)
Transcription Speed: ~2.5s for 10 seconds of speech
Total User Latency: ~4 seconds after stopping
Accuracy: 95%+
Memory Usage: ~600MB

✅ Recommended for: All-purpose dictation
```

### With tiny.en (Fallback)
```
Initial Model Load: ~0.8s (first run only)
Transcription Speed: ~1.2s for 10 seconds of speech
Total User Latency: ~2 seconds after stopping
Accuracy: 85-90%
Memory Usage: ~400MB

✅ Recommended for: Quick notes, casual dictation
⚠️ May struggle with: Technical jargon, heavy accents
```

---

## 🎯 Usage Pattern

### Your Workflow
```
1. Press Ctrl + '
   → 🎙️ "Recording..." notification

2. Speak your text
   → (Red recording indicator in system tray - optional)

3. Press Ctrl + ' again
   → ⏳ "Transcribing..." notification
   → Wait ~2-4 seconds
   → Text appears at cursor
   → ✅ "Complete!" notification with transcribed text
```

---

## 🔧 Customization Notes

### Things You Might Want to Tune Later

**If transcription is slower than expected:**
- Switch to `WHISPER_MODEL="tiny.en"`
- Reduce `WHISPER_BEAM_SIZE=3`

**If accuracy could be better:**
- Try `WHISPER_MODEL="small.en"` (will be slower)
- Add context via `WHISPER_INITIAL_PROMPT="Technical documentation about..."`

**If specific words are consistently wrong:**
- Use `TEXT_REPLACEMENTS="wrongword:rightword,another:fixed"`

**If you want text in clipboard too:**
- Change `PASTE_METHOD="both"` (types AND copies)

---

## 📂 File Locations Reference

```
Workspace Root:
/home/sdx/Files/W/Workspace/git/automation/systemd-automations/

Module Directory:
modules/dictation/

Configuration:
modules/dictation/config/dictation.env

Scripts:
modules/dictation/dictate.py
modules/dictation/dictation-toggle.sh
modules/dictation/setup.sh

Temporary Files:
/tmp/dictation/recording-*.wav

Lock File:
/tmp/dictation.lock

Logs:
~/.local/share/dictation/dictation.log

Whisper Models (cached):
~/.cache/huggingface/hub/
```

---

## 🚀 Quick Commands

### Daily Use
```bash
# Normal use - just press Ctrl + '

# Check if recording is active
ls -la /tmp/dictation.lock

# View recent logs
tail -f ~/.local/share/dictation/dictation.log

# Test without hotkey
cd /home/sdx/Files/W/Workspace/git/automation/systemd-automations/modules/dictation
./dictation-toggle.sh
```

### Troubleshooting
```bash
# Check model is downloaded
ls ~/.cache/huggingface/hub/

# Test faster-whisper directly
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('base.en'); print('OK')"

# Check audio device
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Verify xdotool works
xdotool getactivewindow getwindowname

# Test notification
notify-send "Test" "This is a test"
```

---

## 📋 Checklist for First Run

- [ ] Install dependencies (see SETUP_CHECKLIST.md)
- [ ] Run setup script: `./setup.sh`
- [ ] Configure XFCE hotkey: Ctrl + '
- [ ] Test manual toggle: `./dictation-toggle.sh`
- [ ] Test with hotkey: Press Ctrl + '
- [ ] Verify base.en performance
- [ ] Switch to tiny.en if needed
- [ ] Adjust configuration to taste

---

## 🔖 Bookmarks

Quick links to relevant documentation:

- [Configuration Options Guide](CONFIGURATION_OPTIONS.md) - All settings explained
- [Architecture Summary](ARCHITECTURE_SUMMARY.md) - Design decisions
- [Setup Checklist](SETUP_CHECKLIST.md) - Dependency installation
- [System Profile](SYSTEM_PROFILE.md) - Your hardware/software

---

**Preferences Version:** 1.0  
**Last Updated:** October 26, 2025  
**Status:** Ready for implementation

