# 🖥️ System Profile & Recommendations

**Generated:** October 26, 2025  
**Purpose:** Document system-specific configuration for optimal module design

---

## System Information

```yaml
OS: Manjaro Linux
Kernel: 6.6.107-1-MANJARO
Architecture: x86_64
Desktop Environment: XFCE
Display Server: X11
Audio System: PulseAudio
Shell: /usr/bin/bash
Python: 3.13.7
Package Managers:
  - pacman (native)
  - yay (AUR helper)
```

---

## Hardware Profile

### Audio Devices
```
✓ Blue Microphones USB Audio (Card 2) - Recommended for dictation
  - Professional-grade USB microphone
  - Native PulseAudio support
  
✓ HD-Audio Generic ALC1220 (Card 1) - Fallback
  - Motherboard audio
  - Analog input available
```

### Display
- X11 display server
- XFCE window manager

---

## Software Inventory

### ✅ Pre-installed

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.13.7 | Runtime for automation scripts |
| NumPy | 2.3.3 | Numerical operations (audio processing) |
| notify-send | - | Desktop notifications |
| arecord | - | Audio recording (ALSA) |
| xfconf-query | - | XFCE configuration tool |
| systemd | - | Service management |
| pacman | - | Package manager |
| yay | - | AUR helper |

### ⚠️ Needs Installation

| Package | Install Command | Purpose |
|---------|----------------|---------|
| xdotool | `sudo pacman -S xdotool` | Text injection (X11) |
| portaudio | `sudo pacman -S portaudio` | Audio I/O library |
| sounddevice | `pip install sounddevice` | Python audio capture |
| faster-whisper | `pip install faster-whisper` | Speech recognition |

---

## Architecture Recommendations

### Dictation Module

**Recommended Stack:**
```yaml
Hotkey Trigger: XFCE Native Shortcuts (xfconf-query)
  Reason: Built-in, zero overhead, no extra daemon
  
Audio Capture: sounddevice + PulseAudio
  Reason: Python-native, works with Blue Microphones USB
  
Speech Recognition: faster-whisper (base.en model)
  Reason: 4x faster than OpenAI, easy pip install
  
Text Injection: xdotool
  Reason: Standard for X11, reliable and fast
  
Notifications: notify-send
  Reason: Already installed, XFCE-native
  
State Management: Lock file (/tmp/dictation.lock)
  Reason: Simple IPC, no extra dependencies
```

**Why NOT use:**
- ❌ `keyboard` library - Requires root/sudo
- ❌ `xbindkeys` - Unnecessary daemon when XFCE has native shortcuts
- ❌ `whisper.cpp` - Requires compilation, harder to install
- ❌ `openai-whisper` - 2-4x slower than faster-whisper

---

## Desktop Environment Integration

### XFCE Keyboard Shortcuts

**Native Support:** XFCE provides built-in keyboard shortcut management via `xfce4-keyboard-shortcuts`.

**Configuration Methods:**

1. **GUI (Recommended for testing):**
   ```
   Settings → Keyboard → Application Shortcuts → Add
   ```

2. **CLI (Recommended for automation):**
   ```bash
   xfconf-query -c xfce4-keyboard-shortcuts \
     -p "/commands/custom/<Primary><Alt>space" \
     -n -t string -s "/path/to/script.sh"
   ```

3. **Advantages:**
   - No extra process overhead
   - Survives reboots automatically
   - Integrates with XFCE session
   - Can be version-controlled via xfconf XML exports

---

## Performance Characteristics

### Expected Latency (Dictation Module)

```
Component                    Latency     Notes
─────────────────────────────────────────────────────────
Hotkey Detection            ~5ms        XFCE native, very fast
Script Startup              ~150ms      Python 3.13 cold start
Model Loading (1st time)    ~1000ms     faster-whisper base.en
Recording                   variable    User-dependent
Transcription               0.25x RT    10s audio = 2.5s processing
Text Injection              ~30ms       xdotool on X11
─────────────────────────────────────────────────────────
Total Overhead              ~2.7s       For 10s of speech
```

### Optimization Options

1. **Use smaller model:** `tiny.en` - 8x realtime (3x faster)
2. **Daemon mode:** Pre-load model, eliminate loading time
3. **Audio device:** USB mic (Blue) typically has better quality → better recognition

---

## Module Design Guidelines

Based on system profile, all modules should follow:

### ✅ Do Use
- Python 3.13+ for scripting
- XFCE native tools where available
- X11-compatible tools (xdotool, xclip, etc.)
- PulseAudio/PipeWire compatible audio
- systemd user services for daemons
- notify-send for user feedback
- pacman/yay installation paths

### ❌ Avoid
- Root/sudo requirements in normal operation
- Wayland-only tools (unless fallback provided)
- Extra daemon processes when native alternatives exist
- External cloud services (prioritize local-first)
- Non-standard package sources

### 🎯 Design Patterns
1. **Hotkeys:** Use XFCE shortcuts first, xbindkeys as fallback
2. **Audio:** Use sounddevice + PulseAudio for Python scripts
3. **Notifications:** Use notify-send (libnotify)
4. **Config:** Environment files in `config/` directories
5. **State:** Lock files in `/tmp/` or `$XDG_RUNTIME_DIR`
6. **Installation:** Provide setup scripts that use pacman/yay

---

## systemd Integration

**User Services Available:** ✅ Active

```bash
# Check status
systemctl --user status

# Standard locations
~/.config/systemd/user/          # User service units
/usr/lib/systemd/user/           # System-provided user units
```

**Best Practices:**
- Use user services (not system services) for personal automations
- Set `Type=simple` for long-running processes
- Set `Type=oneshot` for triggered jobs
- Use timers for scheduled tasks
- Include `After=graphical-session.target` for GUI apps

---

## Quick Setup Commands

### Complete System Preparation
```bash
# Update system
sudo pacman -Syu

# Install missing tools
sudo pacman -S xdotool portaudio

# Install Python packages
pip install --user sounddevice faster-whisper

# Verify installations
which xdotool
python3 -c "import sounddevice, faster_whisper; print('Ready!')"
```

---

## Future Considerations

### Wayland Migration
If switching to Wayland in the future:
- Replace xdotool → wtype or ydotool
- XFCE shortcuts may need alternative (wev + custom daemon)
- Test all X11-dependent tools

### Additional Modules
This profile supports:
- ✅ Screen capture automations (X11 tools available)
- ✅ Clipboard managers (xclip/xsel)
- ✅ Window management scripts (xdotool/wmctrl)
- ✅ Audio processing (PulseAudio + Python)
- ✅ File watchers (inotify)
- ✅ Network monitors (standard Linux tools)

---

## Contact & Updates

This profile should be updated when:
- OS or kernel is upgraded
- Desktop environment changes
- Display server migrates to Wayland
- Python version changes
- New audio hardware is added

To regenerate this profile, run:
```bash
./scripts/detect-system.sh > docs/SYSTEM_PROFILE.md
```

---

**Profile Version:** 1.0  
**Last Updated:** October 26, 2025  
**System Owner:** Sidhant Dixit

