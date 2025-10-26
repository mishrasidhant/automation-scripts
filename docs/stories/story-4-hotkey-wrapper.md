# Story 4: Hotkey Wrapper Script & Configuration

**Story ID:** DICT-004  
**Epic:** Dictation Module Implementation  
**Priority:** High (User Interface)  
**Complexity:** Low  
**Estimated Effort:** 1-2 hours  
**Depends On:** Story 3 (Toggle mode)

---

## User Story

**As a** user,  
**I want** to trigger dictation with a single system-wide hotkey,  
**So that** I can dictate text in any application without switching to a terminal.

---

## Story Context

### Existing System Integration

- **Builds on:** Story 3 (complete dictate.py with toggle mode)
- **Technology:** Bash wrapper script, XFCE keyboard shortcuts
- **Hotkey:** Ctrl+' (user's preferred combination)
- **Configuration:** Environment file for user settings

### Technical Approach

Create wrapper infrastructure:
- Bash script that calls `dictate.py --toggle`
- Configuration file for user-customizable settings
- XFCE hotkey binding to trigger wrapper script
- Path resolution for portable installation

---

## Acceptance Criteria

### Functional Requirements

1. **Wrapper script provides simple hotkey interface**
   - Located at: `modules/dictation/dictation-toggle.sh`
   - Executable with proper shebang
   - Calls `dictate.py --toggle` with correct paths
   - Sources configuration from env file

2. **Configuration file enables user customization**
   - Located at: `modules/dictation/config/dictation.env`
   - Contains all user-configurable settings
   - Well-commented with examples
   - Sensible defaults for user's system

3. **XFCE hotkey binding is registered**
   - Hotkey: Ctrl+' (user's preference)
   - Command: Full path to dictation-toggle.sh
   - Persists across reboots
   - Can be changed via XFCE settings GUI

### Integration Requirements

4. **Wrapper script handles path resolution correctly**
   - Works when called from any directory
   - Finds dictate.py relative to script location
   - Sources config file relative to script location
   - No hardcoded absolute paths (except in XFCE binding)

5. **Configuration is read and applied to dictate.py**
   - Whisper model selection (base.en, tiny.en, etc.)
   - Audio device selection (default or specific)
   - Notification preferences
   - Temp directory location
   - Debug mode toggle

6. **Error handling for missing components**
   - If dictate.py missing: error notification
   - If config missing: use defaults, warn user
   - If Python not found: error notification with instructions

### Quality Requirements

7. **Hotkey activation is fast and responsive**
   - Toggle triggers within 200ms of hotkey press
   - No noticeable delay for user
   - XFCE native shortcuts (no extra daemon)

8. **Configuration format is user-friendly**
   - Clear comments explaining each option
   - Examples for common customizations
   - Safe defaults that work out of box

9. **Installation is straightforward**
   - Script is executable out of the box
   - Permissions set correctly (755)
   - Works immediately after setup

---

## Technical Implementation Details

### File Structure (Complete)

```
modules/dictation/
├── dictate.py                   # Core script (Stories 1-3)
├── dictation-toggle.sh          # Wrapper script (this story) ← NEW
└── config/
    └── dictation.env            # Configuration file (this story) ← NEW
```

### dictation-toggle.sh Implementation

```bash
#!/bin/bash
#
# Dictation Toggle Wrapper Script
# Triggers voice-to-text dictation via system hotkey
#
# Usage: Called automatically by XFCE keyboard shortcut (Ctrl+')
#

set -euo pipefail

# Determine script directory (works with symlinks)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# Configuration file
CONFIG_FILE="${SCRIPT_DIR}/config/dictation.env"

# Source configuration (use defaults if missing)
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    # Defaults if config missing
    WHISPER_MODEL="${WHISPER_MODEL:-base.en}"
    WHISPER_DEVICE="${WHISPER_DEVICE:-cpu}"
    ENABLE_NOTIFICATIONS="${ENABLE_NOTIFICATIONS:-true}"
fi

# Python script location
DICTATE_PY="${SCRIPT_DIR}/dictate.py"

# Validate dictate.py exists
if [ ! -f "$DICTATE_PY" ]; then
    if command -v notify-send &> /dev/null && [ "$ENABLE_NOTIFICATIONS" = "true" ]; then
        notify-send "Dictation Error" "Script not found: $DICTATE_PY"
    fi
    echo "ERROR: dictate.py not found at $DICTATE_PY" >&2
    exit 1
fi

# Validate Python is available
if ! command -v python3 &> /dev/null; then
    if command -v notify-send &> /dev/null && [ "$ENABLE_NOTIFICATIONS" = "true" ]; then
        notify-send "Dictation Error" "Python 3 not found. Please install Python."
    fi
    echo "ERROR: python3 not found in PATH" >&2
    exit 1
fi

# Export configuration as environment variables for dictate.py
export WHISPER_MODEL
export WHISPER_DEVICE
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-int8}"
export AUDIO_DEVICE="${AUDIO_DEVICE:-}"
export ENABLE_NOTIFICATIONS
export TEMP_DIR="${TEMP_DIR:-/tmp/dictation}"
export KEEP_TEMP_FILES="${KEEP_TEMP_FILES:-false}"

# Call dictate.py with toggle mode
python3 "$DICTATE_PY" --toggle

# Exit with dictate.py's exit code
exit $?
```

### config/dictation.env Implementation

```bash
#!/bin/bash
#
# Dictation Module Configuration
# Customized for: Sidhant's Manjaro + XFCE + X11 System
#
# This file is sourced by dictation-toggle.sh and provides
# user-configurable settings for the dictation module.
#

# === WHISPER MODEL CONFIGURATION ===

# Model to use for speech recognition
# Options: tiny.en, base.en, small.en, medium.en
# Recommendation: base.en (balanced speed and accuracy)
# Note: First run will download the model (~145MB for base.en)
WHISPER_MODEL="base.en"

# Device to run inference on
# Options: cpu, cuda (requires NVIDIA GPU)
WHISPER_DEVICE="cpu"

# Compute precision (affects speed vs accuracy)
# Options: int8, int16, float16, float32
# Recommendation: int8 (fastest for CPU)
WHISPER_COMPUTE_TYPE="int8"

# === AUDIO INPUT CONFIGURATION ===

# Audio input device (leave empty for system default)
# To list devices: python3 -c "import sounddevice as sd; print(sd.query_devices())"
# Options:
#   "" (empty) = Use system default (recommended)
#   "2" = Specific device index
#   "Blue Microphones" = Device name (partial match)
AUDIO_DEVICE=""

# Sample rate (Hz) - 16000 is optimal for Whisper
SAMPLE_RATE=16000

# Number of audio channels (1=mono, 2=stereo)
CHANNELS=1

# === TEXT PASTING CONFIGURATION ===

# Method for pasting transcribed text
# Options: xdotool, clipboard, both
# Recommendation: xdotool (direct typing for X11)
PASTE_METHOD="xdotool"

# Typing speed (milliseconds between keystrokes)
# Lower = faster, Higher = more reliable for slow apps
TYPING_DELAY=12

# Clear modifier keys before typing (prevents stuck keys)
CLEAR_MODIFIERS=true

# === TEXT PROCESSING ===

# Strip leading/trailing whitespace
STRIP_LEADING_SPACE=true
STRIP_TRAILING_SPACE=true

# Capitalize first letter of transcription
AUTO_CAPITALIZE=false

# Keep Whisper's punctuation
AUTO_PUNCTUATION=true

# Text replacements (format: "pattern1:replacement1,pattern2:replacement2")
# Example: "umm:,uh:,you know:" (removes filler words)
TEXT_REPLACEMENTS=""

# === NOTIFICATIONS ===

# Enable desktop notifications
ENABLE_NOTIFICATIONS=true

# Notification tool (notify-send is standard on XFCE)
NOTIFICATION_TOOL="notify-send"

# Notification urgency: low, normal, critical
NOTIFICATION_URGENCY="normal"

# Notification timeout (milliseconds, 0=default)
NOTIFICATION_TIMEOUT=3000

# Show transcribed text in completion notification
SHOW_TRANSCRIPTION_IN_NOTIFICATION=true

# === FILE MANAGEMENT ===

# Temporary directory for audio files
TEMP_DIR="/tmp/dictation"

# Keep audio files after transcription (for debugging)
KEEP_TEMP_FILES=false

# Lock file location (tracks recording state)
LOCK_FILE="/tmp/dictation.lock"

# === LOGGING (OPTIONAL) ===

# Log file location (leave empty to disable logging)
LOG_FILE=""
# Example: LOG_FILE="$HOME/.local/share/dictation/dictation.log"

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL="INFO"

# === ADVANCED WHISPER SETTINGS ===

# Language hint (helps with accuracy)
WHISPER_LANGUAGE="en"

# Voice Activity Detection (removes silence)
WHISPER_VAD_FILTER=true

# Initial prompt (provides context to Whisper)
# Example: "Technical documentation about Linux systems."
WHISPER_INITIAL_PROMPT=""

# Beam size (higher = more accurate but slower)
WHISPER_BEAM_SIZE=5

# Temperature (0.0 = deterministic, higher = more random)
WHISPER_TEMPERATURE=0.0

# === PERFORMANCE TUNING ===

# If base.en is too slow, uncomment this to use tiny.en:
# WHISPER_MODEL="tiny.en"

# For debugging, keep temporary files:
# KEEP_TEMP_FILES=true
# LOG_FILE="$HOME/.local/share/dictation/dictation.log"
# LOG_LEVEL="DEBUG"
```

### XFCE Hotkey Registration

```bash
# CLI method to register hotkey
xfconf-query -c xfce4-keyboard-shortcuts \
  -p "/commands/custom/<Primary>apostrophe" \
  -n -t string \
  -s "$HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictation-toggle.sh"

# Explanation:
# <Primary> = Ctrl in XFCE notation
# apostrophe = ' key
# Result: Ctrl+' triggers the wrapper script
```

---

## Implementation Checklist

### Phase 1: Wrapper Script Creation
- [ ] Create `dictation-toggle.sh` in modules/dictation/
- [ ] Add shebang and script header
- [ ] Implement path resolution (script directory detection)
- [ ] Add configuration file sourcing
- [ ] Implement dictate.py invocation

### Phase 2: Configuration File Creation
- [ ] Create `config/` directory
- [ ] Create `dictation.env` with all settings
- [ ] Add detailed comments for each option
- [ ] Set sensible defaults for user's system
- [ ] Document model selection guidance

### Phase 3: Error Handling & Validation
- [ ] Check for dictate.py existence
- [ ] Check for Python availability
- [ ] Handle missing config file gracefully
- [ ] Add error notifications for common issues

### Phase 4: XFCE Hotkey Integration
- [ ] Test manual execution of wrapper script
- [ ] Register Ctrl+' hotkey via xfconf-query
- [ ] Test hotkey activation
- [ ] Verify persistence across reboot

### Phase 5: Permissions & Portability
- [ ] Make wrapper script executable (chmod +x)
- [ ] Test execution from different directories
- [ ] Verify config is sourced correctly
- [ ] Test with symlinked script path

---

## Testing Strategy

### Manual Tests

1. **Direct Execution Test**
   ```bash
   cd $HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation
   ./dictation-toggle.sh
   # Should start recording (notification shown)
   ./dictation-toggle.sh
   # Should stop and transcribe (text pasted)
   ```

2. **Path Resolution Test**
   ```bash
   cd /tmp
   $HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictation-toggle.sh
   # Should work from different directory
   ```

3. **Configuration Loading Test**
   ```bash
   # Edit config to use tiny.en
   nano modules/dictation/config/dictation.env
   # Change: WHISPER_MODEL="tiny.en"
   
   ./dictation-toggle.sh
   # Verify tiny.en model is used (faster transcription)
   ```

4. **Hotkey Activation Test**
   ```bash
   # Register hotkey
   xfconf-query -c xfce4-keyboard-shortcuts \
     -p "/commands/custom/<Primary>apostrophe" \
     -n -t string \
     -s "$HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictation-toggle.sh"
   
   # Press Ctrl+' (should start recording)
   # Press Ctrl+' again (should transcribe and paste)
   ```

5. **Error Handling Test**
   ```bash
   # Temporarily rename dictate.py
   mv dictate.py dictate.py.bak
   ./dictation-toggle.sh
   # Should show error notification
   mv dictate.py.bak dictate.py
   ```

6. **Persistence Test**
   ```bash
   # Reboot system
   sudo reboot
   
   # After reboot, press Ctrl+'
   # Should still work (XFCE persists shortcuts)
   ```

---

## Definition of Done

- ✅ Wrapper script exists and is executable
- ✅ Configuration file exists with sensible defaults
- ✅ Wrapper script calls dictate.py correctly
- ✅ Configuration is loaded and applied
- ✅ XFCE hotkey (Ctrl+') triggers dictation
- ✅ Hotkey binding persists across reboots
- ✅ Path resolution works from any directory
- ✅ Error handling shows helpful messages
- ✅ Manual tests all pass
- ✅ Documentation explains config options

---

## Dependencies

### System Dependencies
- XFCE keyboard shortcuts (already present ✓)
- xfconf-query (already present ✓)
- bash (already present ✓)

### Script Dependencies
- dictate.py from Story 3 (prerequisite)
- Python 3 (already present ✓)

### No New Installations Required
All dependencies for this story are already satisfied.

---

## Example Usage (After Implementation)

```bash
# Manual execution (for testing)
$ $HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictation-toggle.sh
🎙️ Recording started...

# (Speak)

$ # Press Ctrl+' (or run script again)
⏳ Transcribing...
✅ Done! Pasted 12 words

# Normal usage: Just press Ctrl+' anywhere, anytime
# First press: Start recording
# Second press: Stop and paste
```

---

## Configuration Examples

### For Faster Speed (Lower Accuracy)
```bash
# In config/dictation.env
WHISPER_MODEL="tiny.en"
WHISPER_BEAM_SIZE=3
```

### For Higher Accuracy (Slower)
```bash
WHISPER_MODEL="small.en"
WHISPER_BEAM_SIZE=7
WHISPER_COMPUTE_TYPE="int16"
```

### For Debugging
```bash
KEEP_TEMP_FILES=true
LOG_FILE="$HOME/.local/share/dictation/dictation.log"
LOG_LEVEL="DEBUG"
```

### For Clipboard Pasting (Instead of Typing)
```bash
PASTE_METHOD="clipboard"
```

---

## Success Metrics

- **Functionality:** Hotkey triggers dictation successfully
- **Responsiveness:** <200ms from keypress to recording start
- **Reliability:** Hotkey works 100% of the time
- **Configuration:** Settings are applied correctly
- **User Experience:** Seamless integration with XFCE

---

## Technical Notes

### XFCE Keyboard Shortcut Notation

| Key | XFCE Notation |
|-----|---------------|
| Ctrl | `<Primary>` |
| Alt | `<Alt>` |
| Shift | `<Shift>` |
| Super (Windows key) | `<Super>` |
| ' (apostrophe) | `apostrophe` |

**User's hotkey:** `<Primary>apostrophe` = Ctrl+'

### Script Path Resolution

Using `readlink -f` ensures:
- Symlinks are resolved to actual file location
- Script can find dictate.py relative to its location
- Works regardless of current working directory

### Environment Variable Inheritance

Wrapper script exports config as environment variables:
```bash
export WHISPER_MODEL="base.en"
# dictate.py reads: os.getenv("WHISPER_MODEL", "base.en")
```

This allows config file to override dictate.py defaults.

---

## Risk Assessment

### Risks

1. **Hotkey conflicts with existing binding**
   - **Mitigation:** XFCE will warn on conflict, user can choose different key
   - **Likelihood:** Low (Ctrl+' is uncommon)

2. **Wrapper script permissions incorrect**
   - **Mitigation:** chmod +x in setup script (Story 5)
   - **Likelihood:** Very Low

3. **XFCE doesn't persist hotkey**
   - **Mitigation:** xfconf-query stores in persistent config
   - **Likelihood:** Very Low (XFCE is designed for this)

4. **Path resolution fails in edge cases**
   - **Mitigation:** Use absolute path in XFCE binding
   - **Likelihood:** Very Low

### Rollback Plan

To remove hotkey:
```bash
xfconf-query -c xfce4-keyboard-shortcuts \
  -p "/commands/custom/<Primary>apostrophe" \
  -r
```

Or use XFCE Settings GUI to delete the shortcut.

---

## Future Integration Points

This story enables:
- **Story 5:** Setup script can register hotkey automatically
- **Story 6:** End-to-end testing with real hotkey
- **User customization:** Easy config editing without code changes

---

## Related Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md` (Hotkey integration section)
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md` (Complete config reference)
- **System Profile:** `docs/SYSTEM_PROFILE.md` (XFCE details)

---

**Story Status:** Ready for Implementation  
**Prerequisites:** Story 3 complete (toggle mode)  
**Blocks:** Story 5 (setup needs to register hotkey)  
**Review Required:** Hotkey activation validation before Story 5

