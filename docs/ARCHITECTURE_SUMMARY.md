# 🏗️ Architecture Update Summary

**Date:** October 26, 2025  
**Module:** Dictation (Voice-to-Text)  
**Status:** Architecture Finalized - Ready for Implementation

---

## 📋 Overview

The dictation module architecture has been **optimized specifically for your Manjaro Linux + XFCE + X11 system** based on comprehensive system detection and analysis.

---

## ✅ Key Decisions

### 1. **Hotkey Management**
**Decision:** Use XFCE native keyboard shortcuts  
**Rationale:** 
- Built into your desktop environment (no extra daemon)
- Zero resource overhead
- Survives reboots automatically
- Simple GUI and CLI configuration

**Rejected Alternatives:**
- ❌ xbindkeys - Unnecessary extra process
- ❌ sxhkd - Primarily for Wayland/tiling WMs
- ❌ keyboard library in Python - Requires root/sudo

---

### 2. **Speech Recognition Engine**
**Decision:** Use `faster-whisper` (Python library)  
**Rationale:**
- 4x faster than official OpenAI whisper
- Easy installation via pip (no compilation)
- Automatic model download
- Lower memory usage
- Native Python integration

**Rejected Alternatives:**
- ❌ whisper.cpp - Requires compilation, more complex
- ❌ openai-whisper - 2-4x slower

---

### 3. **Audio Capture**
**Decision:** Use `sounddevice` + PulseAudio  
**Rationale:**
- Python-native library
- Works seamlessly with PulseAudio
- Compatible with your Blue Microphones USB audio
- Clean API, easy to use

**System Details:**
- Detected: Blue Microphones USB Audio (Card 2)
- Fallback: HD-Audio Generic ALC1220 (Card 1)

---

### 4. **Text Injection**
**Decision:** Use `xdotool`  
**Rationale:**
- Standard tool for X11
- Your system uses X11 (not Wayland)
- Reliable, fast, well-maintained

**Rejected Alternatives:**
- ❌ wtype - Wayland only (not applicable)
- ❌ ydotool - Unnecessary complexity for X11

---

### 5. **Architecture Pattern**
**Decision:** On-Demand Trigger (not persistent daemon)  
**Rationale:**
- No persistent process consuming resources
- No root/sudo privileges needed
- Better separation of concerns
- Easier to debug and maintain
- Slight startup delay (~150ms) is acceptable

**Flow:**
```
User Hotkey → XFCE → dictation-toggle.sh → dictate.py → Transcribe → Paste
```

**Rejected Alternative:**
- ❌ Daemon mode with keyboard library - Security concerns, requires root

---

## 📊 System Profile

Your detected system configuration:

| Component | Value |
|-----------|-------|
| OS | Manjaro Linux (kernel 6.6.107-1) |
| Desktop | XFCE |
| Display Server | X11 |
| Audio System | PulseAudio |
| Python | 3.13.7 |
| Package Manager | pacman + yay (AUR) |
| Microphone | Blue Microphones USB Audio |

**Already Installed:**
- ✅ notify-send
- ✅ arecord
- ✅ numpy (2.3.3)
- ✅ xfconf-query
- ✅ systemd user services

**Needs Installation:**
- ⚠️ xdotool (`sudo pacman -S xdotool`)
- ⚠️ portaudio (`sudo pacman -S portaudio`)
- ⚠️ sounddevice (`pip install sounddevice`)
- ⚠️ faster-whisper (`pip install faster-whisper`)

---

## 🎯 Expected Performance

**Latency Breakdown (for 10s of speech):**
- Hotkey detection: ~5ms
- Script startup: ~150ms
- Model loading (first time): ~1s
- Recording: 10s (variable)
- Transcription: ~2.5s (0.25x realtime)
- Text pasting: ~30ms
- **Total overhead: ~2.7s** (after recording ends)

**Model Options:**

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| tiny.en | 8x RT | 85% | Quick notes |
| base.en | 4x RT | 95% | **Recommended** |
| small.en | 2x RT | 98% | Important docs |
| medium.en | 1x RT | 99% | Professional |

---

## 📁 Module Structure

```
modules/dictation/
├── README.md                    # User-facing documentation
├── dictate.py                   # Core recording + transcription logic
├── dictation-toggle.sh          # Wrapper script for hotkey integration
├── setup.sh                     # Automated setup and dependency checking
└── config/
    └── dictation.env            # User-configurable settings
```

**Key Files:**

1. **dictate.py** - Refactored from staging version
   - Removed keyboard library (no sudo!)
   - Added CLI args: `--start`, `--stop`, `--toggle`
   - Uses faster-whisper instead of whisper.cpp
   - Lock file state management
   - xdotool text pasting

2. **dictation-toggle.sh** - New wrapper script
   - Checks lock file state
   - Calls dictate.py with appropriate args
   - Sources config from env file

3. **config/dictation.env** - Configuration
   - Whisper model selection
   - Audio device settings
   - Notification preferences

4. **setup.sh** - Setup automation
   - Dependency validation
   - Directory creation
   - XFCE hotkey registration
   - Test suite

---

## 🎹 User Experience Flow

```
1. User presses Ctrl+Alt+Space (or custom hotkey)
   └─> XFCE triggers dictation-toggle.sh

2. 🎙️ Notification: "Recording started..."
   └─> dictate.py --start creates lock file
   └─> Begins capturing audio from Blue Microphones

3. User speaks their text...

4. User presses Ctrl+Alt+Space again
   └─> XFCE triggers dictation-toggle.sh

5. ⏳ Notification: "Transcribing..."
   └─> dictate.py --stop processes audio
   └─> faster-whisper transcribes speech
   └─> xdotool types text at cursor

6. ✅ Notification: "Complete!"
   └─> Text appears in active application
   └─> Lock file removed
```

---

## 🔧 Technical Implementation

### Audio Recording
```python
import sounddevice as sd
import wave

# Record from default device (Blue Microphones)
audio = sd.rec(
    int(duration * 16000),
    samplerate=16000,
    channels=1,
    device=None,  # Uses system default
    dtype='int16'
)
sd.wait()

# Save to WAV
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(audio.tobytes())
```

### Speech Recognition
```python
from faster_whisper import WhisperModel

# Load model (cached after first run)
model = WhisperModel(
    "base.en",
    device="cpu",
    compute_type="int8"
)

# Transcribe
segments, info = model.transcribe(
    audio_file,
    language="en"
)
text = " ".join([segment.text for segment in segments])
```

### Text Injection
```python
import subprocess

# Paste text using xdotool
subprocess.run([
    "xdotool",
    "type",
    "--clearmodifiers",  # Avoid stuck modifier keys
    "--",                # End of options
    text
])
```

### Notifications
```python
subprocess.run([
    "notify-send",
    "Dictation",
    "Recording started..."
])
```

---

## 📚 Documentation Created

1. **DICTATION_ARCHITECTURE.md** (480 lines)
   - Complete technical architecture
   - System-specific optimizations
   - Implementation details
   - Performance benchmarks
   - Setup instructions

2. **SYSTEM_PROFILE.md** (245 lines)
   - Hardware inventory
   - Software inventory
   - Architecture recommendations
   - Design guidelines
   - Quick reference

3. **SETUP_CHECKLIST.md** (350 lines)
   - Pre-flight checklist
   - Dependency installation
   - Validation tests
   - Performance baseline
   - Troubleshooting

4. **ARCHITECTURE_SUMMARY.md** (This document)
   - Key decisions and rationale
   - Quick reference guide

---

## 🚀 Next Steps

**Phase 1: Setup Dependencies** ⬅️ Start here
```bash
sudo pacman -S xdotool portaudio
pip install sounddevice faster-whisper
```

**Phase 2: Implementation** (Not started yet)
1. Create `modules/dictation/` structure
2. Refactor `dictate.py` from staging
3. Create `dictation-toggle.sh`
4. Create `config/dictation.env`
5. Create `setup.sh`
6. Write module README.md

**Phase 3: Testing**
1. Run setup checklist
2. Manual testing
3. Hotkey integration
4. Performance validation

**Phase 4: Documentation**
1. User-facing README
2. Configuration examples
3. Troubleshooting guide

---

## 🔄 Changes from Original Staging Script

**Original (`staging/dictate.py`):**
- Used `keyboard` library (requires root!)
- whisper.cpp subprocess calls
- Hardcoded paths
- Daemon mode only
- No configuration file

**New Design:**
- ✅ No keyboard library (no root needed!)
- ✅ faster-whisper Python library
- ✅ Configurable via env file
- ✅ On-demand execution
- ✅ XFCE native hotkeys
- ✅ System-optimized
- ✅ Lock file state management
- ✅ Better error handling

---

## 💡 Design Principles Applied

1. ✅ **Local-first** - All processing on-device
2. ✅ **System-native** - Use XFCE built-in tools
3. ✅ **No root/sudo** - Security best practice
4. ✅ **Configurable** - Easy to customize
5. ✅ **Performant** - Optimized for your system
6. ✅ **Maintainable** - Clean separation of concerns
7. ✅ **Documented** - Comprehensive documentation
8. ✅ **Testable** - Clear validation steps

---

## ⚠️ Important Notes

1. **Universal vs System-Specific:**
   - Architecture prioritizes YOUR system over universal compatibility
   - Alternative approaches documented for reference
   - Can be adapted for other systems if needed

2. **Security:**
   - No root/sudo required in normal operation
   - All processing stays local (no cloud)
   - Temporary files cleaned up automatically

3. **Performance:**
   - First run will download model (~150MB for base.en)
   - Subsequent runs use cached model
   - Can optimize further with tiny.en model

4. **Flexibility:**
   - Can switch to whisper.cpp if preferred
   - Can add daemon mode as optional feature
   - Can use xbindkeys if moving away from XFCE

---

## 📞 Support Resources

**Documentation:**
- `/docs/DICTATION_ARCHITECTURE.md` - Technical deep-dive
- `/docs/SYSTEM_PROFILE.md` - System-specific info
- `/docs/SETUP_CHECKLIST.md` - Pre-flight validation
- `/modules/dictation/README.md` - User guide (TBD)

**External References:**
- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [XFCE Keyboard Docs](https://docs.xfce.org/xfce/xfce4-settings/keyboard)
- [sounddevice Docs](https://python-sounddevice.readthedocs.io/)
- [xdotool Manual](https://www.semicomplete.com/projects/xdotool/)

---

**Summary Version:** 1.0  
**Architecture Status:** ✅ Finalized  
**Implementation Status:** ⏳ Pending (awaiting approval)  
**Estimated Setup Time:** 5-10 minutes  
**Estimated Implementation Time:** 2-3 hours

---

## ✅ Architecture Approval

Architecture has been tailored specifically for:
- ✅ Manjaro Linux + XFCE + X11
- ✅ Blue Microphones USB Audio
- ✅ Python 3.13.7
- ✅ PulseAudio

**Ready to proceed with implementation?** Review the documents above and run the setup checklist to validate your system is ready.

