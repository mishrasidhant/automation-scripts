# Dictation Module - Current State Analysis
## Brownfield Documentation for UV Migration

---

## Document Information

**Purpose:** Document the current state of the dictation module in preparation for UV migration  
**Focus Area:** Dependency management, installation flow, runtime architecture, and known pain points  
**Target Enhancement:** Migrate from venv + pip to UV package manager  
**Document Version:** 1.0  
**Created:** October 27, 2025  
**Author:** Mary (Business Analyst)

---

## Executive Summary

The dictation module is a **fully functional voice-to-text system** built for Manjaro Linux + XFCE + X11. It uses Python with `faster-whisper` AI for speech recognition, triggered via system hotkeys. The module follows a **multi-layered dependency management approach** with system packages (pacman), Python packages (venv + pip), and complex setup orchestration.

**Critical for Migration:** The current dependency management is tightly coupled between:
- Project-wide shared virtual environment (`.venv/`)
- Module-specific requirements (`requirements/dictation.txt`)
- System dependencies (xdotool, portaudio, libnotify)
- XFCE hotkey registration requiring manual xfsettingsd restart

---

## Quick Reference - Critical Files

### Dependency Management Files
- **`requirements/dictation.txt`** - Python package specifications for the module
- **`requirements/base.txt`** - Empty shared requirements (reserved for future)
- **`requirements/all.txt`** - Combined requirements for all modules
- **`requirements/dev.txt`** - Development tools + all module requirements
- **`scripts/setup-dev.sh`** - Project-wide virtual environment setup script
- **`modules/dictation/setup.sh`** - Module-specific automated installation (645 lines)

### Runtime Core Files
- **`modules/dictation/dictate.py`** - Core Python script (1,044 lines)
  - Audio recording (sounddevice)
  - Speech transcription (faster-whisper)
  - Text injection (xdotool)
  - State management via lock files
- **`modules/dictation/dictation-toggle.sh`** - Bash wrapper (90 lines)
  - Configuration loading
  - Environment variable export
  - Hotkey integration point
- **`modules/dictation/config/dictation.env`** - User configuration (137 lines)
  - 30+ configurable parameters
  - Whisper model settings
  - Audio device selection
  - Text processing options

### Integration Files
- **`/tmp/dictation.lock`** - Runtime state tracking (JSON lock file)
- **`/tmp/dictation/`** - Temporary audio recordings
- **XFCE keyboard shortcuts configuration** - Via xfconf-query

---

## Current Dependency Management Architecture

### 1. Three-Layer Dependency Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: System Dependencies (pacman)                   │
│ - xdotool (text injection)                              │
│ - libnotify (desktop notifications)                     │
│ - portaudio (audio backend for sounddevice)             │
│ - python3, pip                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Python Environment (venv + pip)                │
│ Location: .venv/ (project root)                         │
│ - Shared across ALL modules in monorepo                 │
│ - Created by scripts/setup-dev.sh                       │
│ - Managed with pip install -r requirements/*.txt        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Module Requirements                            │
│ File: requirements/dictation.txt                        │
│ - sounddevice>=0.4.6                                    │
│ - numpy>=1.24.0                                         │
│ - faster-whisper>=0.10.0                                │
│ - Includes: -r base.txt (currently empty)               │
└─────────────────────────────────────────────────────────┘
```

### 2. Requirements File Hierarchy

**Current Structure:**
```
requirements/
├── base.txt           # Empty - reserved for universal dependencies
├── dictation.txt      # Module-specific: sounddevice, numpy, faster-whisper
├── all.txt            # Aggregates all module requirements
└── dev.txt            # Development tools + all.txt
```

**Dependencies for Dictation Module:**
```txt
# requirements/dictation.txt
sounddevice>=0.4.6      # Audio recording interface (wraps portaudio)
numpy>=1.24.0           # Audio data arrays
faster-whisper>=0.10.0  # Optimized Whisper AI (CTranslate2-based)
-r base.txt             # Currently empty
```

**Critical Detail:** `faster-whisper` has significant transitive dependencies:
- ctranslate2 (C++ inference engine)
- tokenizers (HuggingFace)
- onnxruntime (for some model operations)
- Plus ~10 other ML/data science packages

### 3. Python Dependency Resolution Strategy

**Current Approach:** Manual, Conservative Versioning
- Uses minimum version specifiers (`>=`)
- No lock file (requirements.txt is not pinned)
- No dependency hash verification
- Relies on pip's resolver (which can vary between installations)

**Installation Commands:**
```bash
# Project-wide setup
source scripts/setup-dev.sh dictation

# Behind the scenes:
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements/dictation.txt
```

### 4. System Dependency Management

**Detection and Installation:** `modules/dictation/setup.sh`
- Lines 110-148: System dependency checking
- Uses `command -v` to test for presence
- Interactive prompts for installation approval
- Automated installation via `sudo pacman -S --needed --noconfirm`

**System Packages Required:**
```bash
python3         # Runtime interpreter
pip             # Python package installer
xdotool         # X11 window automation for text injection
libnotify       # notify-send for desktop notifications
# Note: portaudio is mentioned in comments but not explicitly checked
```

**Pain Point:** System dependency checks are INCOMPLETE
- `portaudio` is required by `sounddevice` but not validated by setup.sh
- Only discovered during Python import if missing
- No version checking (any version assumed compatible)

---

## Installation and Setup Flow

### Entry Points and User Journeys

#### Journey 1: First-Time Module Setup
```bash
cd modules/dictation
./setup.sh
```

**What Happens (645-line script):**

1. **Argument Parsing** (Lines 45-76)
   - Supports `--yes`, `--no-hotkey`, `--skip-tests` flags
   - Non-interactive mode for CI/automation

2. **System Dependency Check** (Lines 110-148)
   ```bash
   check_system_dep "xdotool"
   check_system_dep "notify-send" "libnotify"
   # Missing: portaudio check
   ```

3. **System Package Installation** (Lines 155-185)
   - Interactive prompt: "Install now with pacman? (y/n)"
   - Runs: `sudo pacman -S --needed --noconfirm [packages]`
   - Exit code EXIT_INSTALL_FAILED=2 on failure

4. **Python Environment Setup** (Lines 188-244)
   - Checks for `.venv/` at project root
   - Creates if missing: `python3 -m venv $PROJECT_ROOT/.venv`
   - Upgrades pip: `$VENV_PIP install --upgrade pip`
   - Installs requirements: `$VENV_PIP install -r requirements/dictation.txt`
   - **No version locking** - installs latest compatible versions

5. **Directory Creation** (Lines 251-274)
   ```bash
   mkdir -p /tmp/dictation
   mkdir -p $HOME/.local/share/dictation
   ```

6. **Permissions** (Lines 277-301)
   ```bash
   chmod +x dictation-toggle.sh
   chmod +x dictate.py
   ```

7. **XFCE Hotkey Registration** (Lines 308-371)
   - Default: `<Primary>apostrophe` (Ctrl+')
   - Interactive prompt for custom hotkey
   - Registers via: `xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/$hotkey" -n -t string -s "$script_path"`
   - **KNOWN ISSUE:** Hotkey doesn't persist across reboots (see Pain Points)

8. **Validation Tests** (Lines 378-518)
   - Audio device availability check
   - Whisper model download and loading (first run: ~145MB)
   - xdotool functionality test
   - Wayland detection (fails with clear error if not X11)

#### Journey 2: Development Environment Activation
```bash
source scripts/setup-dev.sh dictation
```

**What Happens (setup-dev.sh):**

1. **Auto-detect or use AUTOMATION_SCRIPTS_DIR** (Line 6)
   ```bash
   PROJECT_ROOT="${AUTOMATION_SCRIPTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
   ```

2. **Create/Activate venv** (Lines 32-49)
   - Creates if missing
   - Activates: `source "$VENV_DIR/bin/activate"`
   - Verifies: `[ "$VIRTUAL_ENV" != "$VENV_DIR" ]`

3. **Module-Specific Install** (Lines 60-75)
   ```bash
   case "$MODULE" in
       dictation|backup|monitoring)
           pip install -r "$PROJECT_ROOT/requirements/$MODULE.txt"
   ```

4. **Display Environment Info** (Lines 108-127)
   - Python path and version
   - Available commands
   - Usage tips

**Pain Point:** No dependency conflict detection between modules
- Installing multiple modules sequentially can cause version conflicts
- No visibility into what changed during installation
- `all.txt` and `dev.txt` attempt to solve this but are manually maintained

---

## Runtime Architecture and File Structure

### Process Model

**Toggle-Based State Machine:**
```
┌──────────────────────────────────────────────────────┐
│ User presses Ctrl+' (XFCE hotkey)                    │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│ XFCE invokes: dictation-toggle.sh                    │
│ - Sources config/dictation.env                       │
│ - Exports 30+ DICTATION_* env vars                   │
│ - Calls: python3 dictate.py --toggle                 │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│ dictate.py handle_toggle() (Lines 801-926)          │
│                                                       │
│ IF lock file exists:                                 │
│   1. Read lock file (/tmp/dictation.lock)           │
│   2. Get PID of recording process                    │
│   3. Send SIGTERM to stop recording                  │
│   4. Wait for audio file to be saved                 │
│   5. Transcribe audio with faster-whisper           │
│   6. Paste text via xdotool                          │
│   7. Clean up lock file and audio (if !debug)       │
│                                                       │
│ ELSE (no lock file):                                 │
│   1. Start new recording process                     │
│   2. Create lock file with PID and metadata          │
│   3. Begin audio capture (sounddevice stream)        │
│   4. Keep process alive until SIGTERM received       │
└──────────────────────────────────────────────────────┘
```

### Lock File as State Tracker

**File:** `/tmp/dictation.lock`  
**Format:** JSON  
**Purpose:** IPC between toggle invocations

**Example Content:**
```json
{
  "pid": 12345,
  "started_at": 1698432000,
  "audio_file": "/tmp/dictation/recording-12345-1698432000.wav",
  "stream_info": {
    "device": "Built-in Microphone",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

**Critical Implementation Details:**
- Lines 478-502: Lock file creation with PID and timestamp
- Lines 611-680: Lock file reading and process termination
- Lines 756-764: Stale lock file cleanup
- **Race Condition Risk:** No file locking mechanism (relies on atomic JSON write)

### Audio Recording Pipeline

**Technology Stack:**
1. **sounddevice** (Python wrapper for portaudio)
   - InputStream with callback function
   - Sample rate: 16000 Hz (optimal for Whisper)
   - Channels: 1 (mono)
   - Data type: int16 (16-bit PCM)

2. **NumPy arrays** for audio buffer
   - Accumulates chunks in `self.audio_data` list
   - Concatenated on stop: `np.concatenate(self.audio_data, axis=0)`

3. **WAV file format**
   - Written with Python's `wave` module
   - 16-bit, 16kHz, mono
   - Saved to: `/tmp/dictation/recording-{PID}-{timestamp}.wav`

**Code Location:** `dictate.py` lines 423-607 (DictationRecorder class)

### Transcription Pipeline

**Technology:** faster-whisper (CTranslate2-based Whisper implementation)

**Model Loading:**
```python
# Lines 226-232
model = WhisperModel(
    model_size_or_path="base.en",    # ~145MB, balanced speed/accuracy
    device="cpu",                     # No GPU support configured
    compute_type="int8",              # Quantized for CPU performance
    cpu_threads=0,                    # Use all cores
    num_workers=1
)
```

**Model Cache Location:** `~/.cache/huggingface/hub/`
- First run: Downloads model (145MB for base.en)
- Subsequent runs: Loads from cache (2-3 seconds)

**Transcription Process:**
```python
# Lines 253-263
segments, info = model.transcribe(
    audio_path,
    language="en",
    beam_size=5,
    temperature=0.0,
    vad_filter=True,                 # Voice Activity Detection
    vad_parameters=dict(min_silence_duration_ms=500)
)
```

**Text Processing Pipeline:**
1. Join segments into single string (Line 260)
2. Strip leading/trailing spaces (Lines 153-156)
3. Optional auto-capitalize (Lines 159-160)
4. Normalize whitespace (Line 163)

**Performance Characteristics:**
- Model loading: 2-3 seconds (from cache)
- Transcription speed: ~3-5x realtime on CPU
  - Example: 10-second audio transcribes in 2-3 seconds
- Total latency from stop to paste: 5-8 seconds

### Text Injection Mechanism

**Primary Method:** xdotool (X11 keyboard simulation)

**Implementation:** `paste_text_xdotool()` (Lines 327-377)

**Process:**
1. **Clear stuck modifiers** (Lines 342-350)
   ```bash
   xdotool keyup Control_L Alt_L Shift_L
   sleep 0.05  # Ensure keys released
   ```

2. **Type text with delay** (Line 357)
   ```bash
   xdotool type --clearmodifiers --delay 12 -- "$text"
   ```
   - `--clearmodifiers`: Prevent Ctrl/Alt/Shift interference
   - `--delay 12`: 12ms between keystrokes (configurable)
   - `--`: Treat everything after as literal text

3. **Fallback mechanisms:**
   - If xdotool fails → Copy to clipboard via xclip/xsel (Lines 380-420)
   - If clipboard fails → Show text in notification (Lines 896-901)

**Known Limitations:**
- Requires X11 (no Wayland support)
- Typing speed is slow for long text (12ms × characters)
- Cannot inject special keys or formatted text
- Active window must accept keyboard input

---

## Configuration System

### Configuration Loading Flow

**Entry Point:** `dictation-toggle.sh` (Lines 14-25)
```bash
CONFIG_FILE="${SCRIPT_DIR}/config/dictation.env"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"  # Bash variable assignment
else
    # Use inline defaults
    WHISPER_MODEL="${WHISPER_MODEL:-base.en}"
fi
```

**Environment Variable Export:** (Lines 48-83)
```bash
export DICTATION_WHISPER_MODEL="${DICTATION_WHISPER_MODEL:-base.en}"
export DICTATION_WHISPER_DEVICE="${DICTATION_WHISPER_DEVICE:-cpu}"
# ... 30+ more variables ...
```

**Python Configuration Loading:** `dictate.py` (Lines 48-104)
```python
def load_config():
    """Load configuration from environment variables with defaults."""
    config = {
        'model': os.environ.get('DICTATION_WHISPER_MODEL', 'base.en'),
        'device': os.environ.get('DICTATION_WHISPER_DEVICE', 'cpu'),
        # ... 30+ more settings ...
    }
    return config

CONFIG = load_config()  # Loaded once at module level
```

### Configuration Categories

**30+ Configurable Parameters organized as:**

1. **Whisper Model Settings** (6 params)
   - Model size: tiny.en, base.en, small.en, medium.en
   - Device: cpu, cuda
   - Compute type: int8, int16, float16, float32
   - Language, beam size, temperature

2. **Audio Configuration** (3 params)
   - Device selection (default or specific)
   - Sample rate: 16000 Hz
   - Channels: 1 (mono)

3. **Text Processing** (6 params)
   - Strip leading/trailing spaces
   - Auto-capitalize
   - Auto-punctuation
   - Text replacements
   - Paste method (xdotool, clipboard)
   - Typing delay

4. **Notifications** (5 params)
   - Enable/disable
   - Tool (notify-send)
   - Urgency level
   - Timeout
   - Show transcription in notification

5. **File Management** (4 params)
   - Temp directory location
   - Keep temp files (debug mode)
   - Lock file location
   - Log file location

6. **Advanced Whisper** (6+ params)
   - VAD filter settings
   - Initial prompt (context)
   - Beam size, temperature
   - Language detection override

**Configuration File Location:** `modules/dictation/config/dictation.env`
- Well-documented with inline comments
- Organized by category
- Includes examples and recommendations

---

## Keyboard Shortcut Registration Mechanism

### XFCE Keyboard Shortcuts System

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│ xfsettingsd (XFCE Settings Daemon)                      │
│ - Monitors keyboard events                              │
│ - Matches against registered shortcuts                  │
│ - Spawns command when hotkey pressed                    │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Configuration Storage: XML file                         │
│ ~/.config/xfce4/xfconf/xfce-perchannel-xml/            │
│   xfce4-keyboard-shortcuts.xml                          │
│                                                          │
│ <property name="&lt;Primary&gt;apostrophe"              │
│           type="string"                                 │
│           value="/path/to/dictation-toggle.sh"/>        │
└─────────────────────────────────────────────────────────┘
```

### Registration Process

**Tool:** xfconf-query (XFCE configuration interface)

**Implementation:** `modules/dictation/setup.sh` (Lines 308-371)

**Process:**
1. **Interactive hotkey selection** (Lines 319-337)
   - Default: `<Primary>apostrophe` (Ctrl+')
   - Prompt user for custom hotkey
   - Format: `<Primary>`, `<Alt>`, `<Shift>`, `<Super>` + key

2. **Registration command** (Lines 351-354)
   ```bash
   xfconf-query -c xfce4-keyboard-shortcuts \
       -p "/commands/custom/$hotkey" \
       -n -t string \
       -s "$script_path"
   ```
   - `-c`: Channel (xfce4-keyboard-shortcuts)
   - `-p`: Property path
   - `-n`: Create new property
   - `-t string`: Type
   - `-s`: Value (script path)

3. **Verification** (Lines 356-370)
   - Success: Display human-readable hotkey
   - Failure: Instruct manual registration via GUI

### The Persistence Problem

**CRITICAL PAIN POINT:** Hotkey doesn't persist across reboots

**Root Cause Analysis:**
1. `xfconf-query` successfully writes to XML configuration
2. XML file is updated immediately and persists
3. **BUT:** `xfsettingsd` (settings daemon) doesn't reload configuration
4. On reboot, xfsettingsd loads old configuration state
5. New hotkey is "forgotten"

**Current Workaround:** Manual xfsettingsd restart required
```bash
# Kill settings daemon
pkill xfsettingsd

# Start fresh instance (reads updated XML)
xfsettingsd &
```

**Why This Is Painful:**
- Users must manually restart daemon after setup.sh
- Setup script cannot automate this (killing user session daemon is risky)
- No automated verification that hotkey works post-reboot
- Documented in post_restart_checklist.md but easy to forget

**Attempted Solutions (per docs/stories/):**
- Investigated `xfconf-query --reload` (doesn't exist)
- Considered `systemctl --user restart xfsettingsd` (not a systemd service)
- Evaluated D-Bus signals to xfsettingsd (no documented API)

**Known Limitation:** This is an XFCE ecosystem limitation, not a bug in dictation module

---

## Known Pain Points and Technical Debt

### 1. Hotkey Persistence Issue

**Severity:** HIGH  
**Impact:** User must manually restart xfsettingsd after setup  
**Workaround:** `pkill xfsettingsd && xfsettingsd &`  
**Files Affected:** `modules/dictation/setup.sh`, `post_restart_checklist.md`

**Technical Details:**
- xfconf-query writes to XML but doesn't trigger daemon reload
- No programmatic way to force xfsettingsd to reload
- Requires user to log out/in OR manually restart daemon

**UV Migration Consideration:** This issue is independent of package management

---

### 2. Multi-Step Setup Process

**Severity:** MEDIUM  
**Impact:** Complex 645-line setup script, multiple user interactions

**Current Steps:**
1. Install system dependencies (requires sudo)
2. Create Python virtual environment
3. Install Python packages
4. Create directories
5. Set permissions
6. Register hotkey
7. Run validation tests

**Pain Points:**
- Setup.sh is monolithic (645 lines, 8 major sections)
- Interactive prompts can't be fully automated
- No resume capability if step fails
- No rollback mechanism

**UV Migration Opportunity:** Could simplify Python dependency installation steps

---

### 3. Incomplete System Dependency Validation

**Severity:** MEDIUM  
**Impact:** portaudio not checked, only fails on Python import

**Missing from setup.sh:**
- No explicit portaudio check
- No version validation for system packages
- Only tests for command existence, not functionality

**Example Failure Mode:**
```bash
./setup.sh  # Passes all checks
python3 dictate.py --start  # ImportError: sounddevice requires portaudio
```

**UV Migration Consideration:** System dependency management is orthogonal to Python packaging

---

### 4. Shared Virtual Environment

**Severity:** MEDIUM  
**Impact:** Potential version conflicts between modules

**Current Design:**
- Single `.venv/` at project root
- Shared by ALL modules (dictation, backup, monitoring, etc.)
- No isolation between modules

**Risk Scenario:**
```bash
source scripts/setup-dev.sh dictation  # Installs numpy>=1.24.0
source scripts/setup-dev.sh monitoring  # Requires numpy>=2.0.0
# dictation module may break if API changed
```

**Mitigation:** `all.txt` and `dev.txt` attempt to specify compatible versions
- **BUT:** Manually maintained, no automated conflict detection

**UV Migration Opportunity:** UV supports per-project and per-module environments

---

### 5. No Dependency Locking

**Severity:** MEDIUM  
**Impact:** Non-reproducible installations, potential breakage

**Current State:**
- Requirements use minimum version specifiers (`>=`)
- No lock file (like requirements.lock, poetry.lock, Pipfile.lock)
- pip install can get different versions on different machines
- No hash verification

**Example Risk:**
```bash
# Developer machine (Oct 2025)
pip install faster-whisper>=0.10.0  # Gets 0.10.5

# Production machine (Nov 2025)
pip install faster-whisper>=0.10.0  # Gets 0.11.0 (breaking change)
```

**UV Migration Opportunity:** UV creates lock files by default (uv.lock)

---

### 6. X11-Only Limitation

**Severity:** HIGH (for Wayland users)  
**Impact:** Module completely non-functional on Wayland

**Affected Components:**
- xdotool (X11 keyboard injection)
- xfconf-query (XFCE configuration)

**Detection:** setup.sh Lines 456-480
```bash
if [ -n "$WAYLAND_DISPLAY" ]; then
    print_status error "xdotool requires X11 - currently running on Wayland"
    # Setup fails with clear error
fi
```

**UV Migration Consideration:** Unrelated to package management

---

### 7. No Automated Testing in CI

**Severity:** LOW  
**Impact:** Manual testing required, no regression prevention

**Current State:**
- `test_dictate.py` exists (pytest suite)
- `test-dictation.sh` exists (integration tests)
- **BUT:** No CI/CD pipeline configured
- Tests must be run manually before releases

**UV Migration Opportunity:** UV integrates well with CI workflows

---

## Python Dependencies Deep Dive

### Direct Dependencies

**From requirements/dictation.txt:**

1. **sounddevice >= 0.4.6**
   - Purpose: Python interface to portaudio
   - Provides: Audio recording/playback API
   - System requirement: portaudio library
   - Size: ~50KB (Python wrapper only)

2. **numpy >= 1.24.0**
   - Purpose: Audio data arrays and mathematical operations
   - Used for: Buffer accumulation, array concatenation
   - Size: ~20MB (compiled C extensions)

3. **faster-whisper >= 0.10.0**
   - Purpose: Optimized Whisper speech recognition
   - Implementation: CTranslate2 (C++ inference engine)
   - Size: ~30MB package, ~145MB model download
   - Performance: 3-5x faster than openai-whisper

### Transitive Dependencies (faster-whisper)

**Significant subdependencies:**
- **ctranslate2** (~100MB) - C++ inference engine
- **tokenizers** (~10MB) - HuggingFace tokenization
- **onnxruntime** (~50MB) - Optional, for some operations
- **huggingface-hub** (~5MB) - Model downloading
- **av** (~20MB) - Audio/video handling
- **tqdm** (~100KB) - Progress bars

**Total installed size:** ~350-400MB (including model cache)

### Dependency Resolution Challenges

**Current pip behavior:**
```bash
pip install faster-whisper>=0.10.0
# Resolves to:
#   faster-whisper==0.10.5
#   ctranslate2==4.1.0
#   tokenizers==0.15.0
#   numpy==1.26.2 (may conflict with existing)
#   ... 15+ more packages
```

**Conflict Risk:**
- numpy version may be upgraded/downgraded
- No visibility into what changed
- No rollback capability

**UV Migration Benefit:** Explicit dependency tree with conflict resolution

---

## System Dependencies

### Required Arch/Manjaro Packages

**Explicitly Checked by setup.sh:**

1. **python3** - Python 3.x interpreter
   - Minimum version: 3.8 (implicit)
   - Used by: All Python scripts

2. **pip** - Python package installer
   - Used by: setup.sh, setup-dev.sh

3. **xdotool** - X11 automation tool
   - Purpose: Keyboard event injection
   - Used by: dictate.py paste_text_xdotool()

4. **libnotify** (provides notify-send)
   - Purpose: Desktop notifications
   - Used by: Recording start/stop, transcription status

**Implicitly Required (not checked):**

5. **portaudio** - Cross-platform audio I/O library
   - Purpose: Backend for sounddevice
   - Not checked by setup.sh
   - Failure mode: Import error in Python

**XFCE-Specific:**

6. **xfconf-query** - XFCE configuration tool
   - Purpose: Hotkey registration
   - Part of xfce4-conf package

7. **xfsettingsd** - XFCE settings daemon
   - Purpose: Hotkey monitoring and execution
   - Part of xfce4-settings package

### Installation Commands

**As root/sudo:**
```bash
pacman -S python3 python-pip xdotool libnotify portaudio
```

**UV Migration Consideration:** System dependencies are unchanged by UV adoption

---

## File System Layout

### Project Structure
```
automation-scripts/
├── .venv/                          # Shared Python virtual environment
│   ├── bin/
│   │   ├── python3                 # Python interpreter
│   │   ├── pip                     # Package installer
│   │   └── pytest                  # Test runner (if dev.txt)
│   ├── lib/python3.11/site-packages/
│   │   ├── sounddevice/
│   │   ├── numpy/
│   │   ├── faster_whisper/
│   │   └── ... (transitive deps)
│   └── pyvenv.cfg                  # venv configuration
│
├── scripts/
│   └── setup-dev.sh                # Project-wide venv activation
│
├── requirements/
│   ├── base.txt                    # Empty (reserved)
│   ├── dictation.txt               # Module requirements
│   ├── all.txt                     # Combined module requirements
│   └── dev.txt                     # Dev tools + all
│
└── modules/dictation/
    ├── dictate.py                  # Core Python script (1,044 lines)
    ├── dictation-toggle.sh         # Bash wrapper (90 lines)
    ├── setup.sh                    # Module installer (645 lines)
    ├── test_dictate.py             # Unit tests (pytest)
    ├── config/
    │   └── dictation.env           # User configuration (137 lines)
    ├── README.md                   # User guide
    └── MANUAL_TESTING.md           # Test procedures
```

### Runtime Filesystem Usage

**Temporary Files:**
```
/tmp/dictation/                      # Audio recordings
├── recording-12345-1698432000.wav   # Format: recording-{PID}-{timestamp}.wav
└── recording-12346-1698432010.wav

/tmp/dictation.lock                  # Process state (JSON)
```

**User Data:**
```
~/.local/share/dictation/            # Reserved for future use (logs, history)

~/.cache/huggingface/hub/            # Whisper model cache
└── models--Systran--faster-whisper-base.en/
    ├── snapshots/
    │   └── .../
    │       ├── model.bin            # ~145MB
    │       ├── vocabulary.txt
    │       └── config.json
```

**Configuration:**
```
~/.config/xfce4/xfconf/xfce-perchannel-xml/
└── xfce4-keyboard-shortcuts.xml     # XFCE hotkey registry
```

---

## UV Migration Preparation - Gap Analysis

### Current State vs UV Capabilities

| Aspect | Current (venv + pip) | UV Target | Migration Complexity |
|--------|---------------------|-----------|---------------------|
| **Lock File** | None | uv.lock | LOW - UV creates automatically |
| **Dependency Resolution** | pip resolver | UV resolver (Rust-based) | LOW - UV handles |
| **Installation Speed** | Slow (~2-3 min) | Fast (<30 sec) | BENEFIT |
| **Reproducibility** | Poor (no locking) | Excellent (hash verification) | BENEFIT |
| **Shared venv** | Manual (.venv/) | Per-project/workspace | MEDIUM - Decision needed |
| **Requirements format** | requirements.txt | pyproject.toml + uv.lock | MEDIUM - File migration |
| **System deps** | pacman (manual) | pacman (still manual) | NO CHANGE |
| **Multi-module support** | Fragile (shared venv) | Strong (workspace support) | BENEFIT |

### Files That Will Need Migration

**To Create:**
- `pyproject.toml` - Project metadata and dependencies
- `uv.lock` - Locked dependency tree (auto-generated)
- `.python-version` - Python version pinning (optional)

**To Modify:**
- `scripts/setup-dev.sh` - Replace venv+pip logic with UV
- `modules/dictation/setup.sh` - Update Python env setup section (lines 188-244)

**To Consider Removing:**
- `requirements/dictation.txt` - Replaced by pyproject.toml
- `requirements/all.txt` - UV workspace handles this
- `requirements/dev.txt` - UV dev dependencies in pyproject.toml

**To Keep Unchanged:**
- `dictate.py` - Pure Python code, no dependency on installer
- `dictation-toggle.sh` - Bash script, unaffected
- `config/dictation.env` - Configuration, unaffected
- System dependency installation - Still uses pacman

### Key Migration Decisions

**Decision 1: Workspace Structure**
- **Option A:** Monorepo with UV workspace
  - Single pyproject.toml at root with workspace members
  - `workspace.members = ["modules/dictation", "modules/backup"]`
  - Shared lock file for all modules
- **Option B:** Independent module projects
  - Each module has its own pyproject.toml and uv.lock
  - Full isolation between modules
- **Recommendation:** Option A - Better for development, shared base dependencies

**Decision 2: Virtual Environment Location**
- **Current:** `.venv/` at project root
- **UV default:** `.venv/` at project root (compatible!)
- **Action:** Keep current location, minimal disruption

**Decision 3: Dev vs Production Requirements**
- **Current:** Separate dev.txt
- **UV approach:** Optional dev dependencies in pyproject.toml
  ```toml
  [project.optional-dependencies]
  dev = ["pytest", "ruff", "mypy"]
  ```
- **Action:** Migrate dev.txt to optional-dependencies

**Decision 4: Python Version Management**
- **Current:** Uses system python3 (whatever version available)
- **UV capability:** Can install and manage Python versions
- **Recommendation:** Specify minimum Python version but let users manage installation

### Risk Assessment

**LOW RISK:**
- Dependency resolution (UV is more robust than pip)
- Installation speed (UV is faster)
- Lock file creation (automatic)

**MEDIUM RISK:**
- Setup script migration (bash script complexity)
- Multi-module shared dependencies (need to validate workspace approach)
- User migration experience (need documentation)

**HIGH RISK:**
- System dependency handling (unchanged, existing complexity remains)
- XFCE hotkey registration (unchanged, existing bug remains)

**MITIGATION:**
- Keep requirements/*.txt files temporarily for rollback capability
- Update documentation with UV commands
- Test on clean system before production migration

---

## Integration Test Scenarios

### Current Manual Test Procedures

**From MANUAL_TESTING.md:**

1. **Basic Recording Test**
   ```bash
   python3 dictate.py --start
   # Speak for 5 seconds
   python3 dictate.py --stop
   # Verify: audio file created in /tmp/dictation/
   ```

2. **Transcription Test**
   ```bash
   python3 dictate.py --transcribe /tmp/dictation/recording-*.wav
   # Verify: text printed to stdout
   ```

3. **Toggle Test**
   ```bash
   python3 dictate.py --toggle  # Start recording
   python3 dictate.py --toggle  # Stop and paste
   # Verify: text appears in active application
   ```

4. **Hotkey Test**
   ```bash
   # Press Ctrl+'
   # Speak
   # Press Ctrl+' again
   # Verify: text pasted
   ```

5. **System Integration Test**
   ```bash
   ./test-dictation.sh
   # Runs automated checks for all components
   ```

### What Needs Testing After UV Migration

**Python Environment:**
- [ ] UV creates virtual environment correctly
- [ ] All dependencies install without errors
- [ ] Dependency tree resolves consistently
- [ ] Lock file includes all transitive dependencies

**Runtime Functionality:**
- [ ] dictate.py can import all packages (sounddevice, numpy, faster_whisper)
- [ ] Whisper model downloads and loads successfully
- [ ] Audio recording works with sounddevice
- [ ] Text injection works with xdotool
- [ ] Configuration loading works (dictation.env → Python)

**Setup Scripts:**
- [ ] setup.sh completes without errors with UV
- [ ] setup-dev.sh activates UV environment correctly
- [ ] Hotkey registration still works (unchanged)

**Cross-Module:**
- [ ] Installing multiple modules doesn't cause conflicts
- [ ] all.txt equivalent (UV workspace) resolves correctly

---

## Conclusion and Next Steps

### Current State Summary

The dictation module is a **functional, well-architected system** with:
- ✅ Comprehensive 645-line setup script
- ✅ Robust 1,044-line Python core
- ✅ 30+ configuration parameters
- ✅ Clear separation of concerns (recording → transcription → injection)
- ✅ Good user documentation

**However**, it suffers from:
- ❌ No dependency locking (non-reproducible installs)
- ❌ Complex multi-step setup process
- ❌ Shared venv with potential conflicts
- ❌ XFCE hotkey persistence bug
- ❌ Incomplete system dependency validation

### UV Migration Readiness

**READY FOR MIGRATION:**
- Dependency specifications are clear and versioned
- Virtual environment location is UV-compatible
- Pure Python code has no installer-specific logic

**MIGRATION BENEFITS:**
- ✅ Dependency locking and reproducibility
- ✅ Faster installation (Rust-based resolver)
- ✅ Better multi-module support (workspaces)
- ✅ Hash verification for security
- ✅ Improved conflict detection

**MIGRATION CHALLENGES:**
- ⚠️ Setup script complexity (645 lines of bash)
- ⚠️ Multi-module shared environment strategy
- ⚠️ User migration documentation

**UNCHANGED BY UV:**
- System dependencies (still require pacman)
- XFCE hotkey registration (still requires xfconf-query)
- Hotkey persistence bug (XFCE limitation, not Python)
- X11 requirement (xdotool limitation, not Python)

### Recommended Migration Approach

**Phase 1: Preparation**
1. Create pyproject.toml with current dependencies
2. Set up UV workspace structure for monorepo
3. Generate initial uv.lock
4. Test on development machine

**Phase 2: Script Migration**
1. Update setup-dev.sh to use UV commands
2. Update modules/dictation/setup.sh Python section
3. Keep requirements/*.txt as fallback temporarily

**Phase 3: Testing**
1. Clean system test (fresh Manjaro VM)
2. Validate all manual test procedures
3. Test multi-module installation

**Phase 4: Documentation**
1. Update README.md with UV commands
2. Update ENVIRONMENT_SETUP.md
3. Create migration guide for existing users

**Phase 5: Rollout**
1. Merge to main branch
2. Tag as v0.1.0 (UV migration)
3. Monitor for issues
4. Remove requirements/*.txt after stability period

---

## Appendix A - Key Command Reference

### Current Commands (venv + pip)

```bash
# Development environment setup
source scripts/setup-dev.sh dictation

# Module installation
cd modules/dictation && ./setup.sh

# Manual testing
python3 dictate.py --start
python3 dictate.py --stop
python3 dictate.py --toggle

# Transcribe audio file
python3 dictate.py --transcribe audio.wav

# Run test suite
pytest test_dictate.py

# Check dependencies
pip list
```

### Future Commands (UV - Proposed)

```bash
# Development environment setup
uv sync
source .venv/bin/activate

# Module installation
cd modules/dictation && ./setup.sh  # Modified for UV

# Runtime commands (unchanged)
python3 dictate.py --start
python3 dictate.py --toggle

# Dependency management
uv add faster-whisper  # Add new dependency
uv lock                 # Update lock file
uv pip list            # Show installed packages
```

---

## Appendix B - Configuration Variables

### All 30+ DICTATION_* Environment Variables

**Whisper Model Configuration:**
- `DICTATION_WHISPER_MODEL` - Model size (default: base.en)
- `DICTATION_WHISPER_DEVICE` - cpu or cuda (default: cpu)
- `DICTATION_WHISPER_COMPUTE_TYPE` - int8, int16, float16, float32 (default: int8)
- `DICTATION_WHISPER_LANGUAGE` - Language code (default: en)
- `DICTATION_WHISPER_BEAM_SIZE` - Search beam size (default: 5)
- `DICTATION_WHISPER_TEMPERATURE` - Sampling temperature (default: 0.0)
- `DICTATION_WHISPER_VAD_FILTER` - Voice activity detection (default: true)
- `DICTATION_WHISPER_INITIAL_PROMPT` - Context prompt (default: empty)

**Audio Configuration:**
- `DICTATION_AUDIO_DEVICE` - Device name/index (default: system default)
- `DICTATION_SAMPLE_RATE` - Sample rate Hz (default: 16000)
- `DICTATION_CHANNELS` - Audio channels (default: 1)

**Text Processing:**
- `DICTATION_PASTE_METHOD` - xdotool, clipboard, both (default: xdotool)
- `DICTATION_TYPING_DELAY` - ms between keystrokes (default: 12)
- `DICTATION_CLEAR_MODIFIERS` - Clear stuck keys (default: true)
- `DICTATION_STRIP_LEADING_SPACE` - Strip leading whitespace (default: true)
- `DICTATION_STRIP_TRAILING_SPACE` - Strip trailing whitespace (default: true)
- `DICTATION_AUTO_CAPITALIZE` - Capitalize first letter (default: false)
- `DICTATION_AUTO_PUNCTUATION` - Keep Whisper punctuation (default: true)
- `DICTATION_TEXT_REPLACEMENTS` - Pattern:replacement pairs (default: empty)

**Notifications:**
- `DICTATION_ENABLE_NOTIFICATIONS` - Show notifications (default: true)
- `DICTATION_NOTIFICATION_TOOL` - notify-send or custom (default: notify-send)
- `DICTATION_NOTIFICATION_URGENCY` - low, normal, critical (default: normal)
- `DICTATION_NOTIFICATION_TIMEOUT` - ms duration (default: 3000)
- `DICTATION_SHOW_TRANSCRIPTION_IN_NOTIFICATION` - Show text (default: true)

**File Management:**
- `DICTATION_TEMP_DIR` - Audio file location (default: /tmp/dictation)
- `DICTATION_KEEP_TEMP_FILES` - Debug mode (default: false)
- `DICTATION_LOCK_FILE` - State file location (default: /tmp/dictation.lock)
- `DICTATION_LOG_FILE` - Log location (default: empty/disabled)
- `DICTATION_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR (default: INFO)
- `DICTATION_DEBUG` - Legacy debug flag (default: false)

---

## Document Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-27 | 1.0 | Initial brownfield analysis for UV migration | Mary (Business Analyst) |

---

**End of Document**

