# Dictation Module Architecture

This document provides a comprehensive technical overview of the dictation module's architecture, design decisions, and component interactions.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Configuration System](#configuration-system)
- [Signal Handling](#signal-handling)
- [UV Environment Management](#uv-environment-management)
- [Systemd Integration](#systemd-integration)
- [Design Decisions](#design-decisions)

## System Overview

The dictation module provides local, offline voice-to-text transcription with seamless desktop integration. The system is designed around several key principles:

**Local-First**: All processing happens on the user's machine. No cloud services, no network dependencies (after initial model download).

**Reliable**: Hotkey integration persists across reboots via systemd service. Recording state is managed with lock files to prevent conflicts.

**Modular**: Clear separation between configuration, audio processing, transcription, and text injection.

**Fast**: UV package management provides instant environment syncing. Optimized Whisper models deliver quick transcription.

### High-Level Flow

```
User Action (Ctrl+')
    ↓
[XFCE Keyboard Daemon]
    ↓
[systemd service] - dictation-hotkey.service (ensures hotkey registered)
    ↓
[Shell Script] - dictation-toggle.sh (state management, lock files)
    ↓
[UV Environment] - auto-sync if needed
    ↓
[Python Module] - automation_scripts.dictation
    ├── config.py - Load configuration (TOML + env vars)
    ├── dictate.py - Audio recording
    ├── dictate.py - Whisper transcription
    └── dictate.py - Text injection (xdotool)
    ↓
[Desktop] - Text appears at cursor
```

## Component Architecture

### 1. Systemd Service Layer

**File**: `systemd/dictation-hotkey.service`

**Purpose**: Ensures the keyboard shortcut is registered on every login and survives reboots.

**Type**: `oneshot` service with `RemainAfterExit=yes`

**Why oneshot?** The service only needs to register the hotkey once per session. It doesn't need to stay running as a daemon.

**Key features:**
- Runs after `xfce4-session.target` (ensures XFCE is ready)
- Uses absolute paths (no assumptions about $PATH)
- Reloads XFCE settings daemon with SIGHUP
- Logs to systemd journal for debugging

**Service Definition:**
```ini
[Unit]
Description=Register Ctrl+' hotkey for dictation
After=xfce4-session.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/user/.local/bin/register-hotkey.sh
ExecReload=/usr/bin/killall -HUP xfce4-settings-helper

[Install]
WantedBy=default.target
```

### 2. Shell Wrapper Layer

**File**: `scripts/dictation-toggle.sh`

**Purpose**: State management, lock file handling, and Python module invocation.

**Responsibilities:**
- Check if recording is in progress (via lock file)
- Start recording: Create lock file, invoke Python module
- Stop recording: Remove lock file, invoke Python module, show notification
- Environment validation: Ensure UV environment is synced
- Logging: All operations logged to `/tmp/dictation-toggle.log`

**Lock File**: `/tmp/dictation.lock`
- Prevents multiple simultaneous recordings
- Contains PID for orphan detection
- Cleaned up on normal exit or SIGTERM

**Why a shell script?** 
- Simple state management with file-based locks
- Easy integration with desktop environment hotkeys
- Minimal overhead for toggling
- Handles UV environment activation transparently

### 3. Python Package Layer

**Location**: `src/automation_scripts/dictation/`

**Structure:**
```
dictation/
├── __init__.py         # Package entry point, main() function
├── __main__.py         # CLI entry point
├── config.py           # Configuration loading and validation
├── constants.py        # XDG paths and default values
└── dictate.py          # Core dictation logic
```

#### 3.1 Configuration Module (`config.py`)

**Purpose**: Load and validate configuration from multiple sources with proper precedence.

**Precedence (highest to lowest):**
1. Environment variables (`DICTATION_*`)
2. TOML file (`~/.config/automation-scripts/dictation.toml`)
3. Built-in defaults (from `constants.py`)

**Key Functions:**
- `load_config()` - Main entry point, returns merged configuration
- `load_toml_config()` - Parse TOML file if it exists
- `apply_env_overrides()` - Apply environment variable overrides
- `validate_config()` - Validate all configuration values
- `merge_config()` - Recursively merge configuration dictionaries

**Type Conversion:**
Environment variables are strings, but config values have types. Automatic conversion:
- `DICTATION_BEAM_SIZE=5` → `int(5)`
- `DICTATION_NOTIFICATIONS_ENABLED=true` → `bool(True)`
- `DICTATION_TEMPERATURE=0.5` → `float(0.5)`

**Validation:**
- Whisper model names (tiny.en, base.en, small.en, medium.en, large)
- Device types (cpu, cuda, auto)
- Compute types (int8, int16, float16, float32)
- Beam size range (1-10)
- Sample rate (must be 16000 Hz for Whisper)
- Channels (must be 1/mono for Whisper)
- Paste methods (xdotool, clipboard, both)
- Typing delay range (0-1000 ms)
- Notification urgency (low, normal, critical)

Validation errors raise `ConfigurationError` with helpful messages.

#### 3.2 Constants Module (`constants.py`)

**Purpose**: Define XDG-compliant paths and default configuration values.

**XDG Base Directories:**
```python
XDG_CONFIG_HOME = ~/.config
XDG_DATA_HOME = ~/.local/share
XDG_CACHE_HOME = ~/.cache

# Application directories
CONFIG_DIR = ~/.config/automation-scripts
DATA_DIR = ~/.local/share/automation-scripts/dictation
CACHE_DIR = ~/.cache/automation-scripts/dictation
MODEL_CACHE_DIR = ~/.cache/automation-scripts/dictation/models
```

**Why XDG?**
- Standard Linux directory structure
- Respects user's environment settings
- Easy to back up (config) vs. cache (disposable)
- Clean separation of concerns

**Directory Creation:**
All directories are created automatically on module import with proper permissions (0o700 for config).

**Default Configuration:**
Complete default configuration dictionary (`DEFAULT_CONFIG`) with sensible values for all settings.

**Environment Variable Mapping:**
Maps environment variables to configuration keys:
```python
ENV_VAR_MAPPING = {
    'DICTATION_WHISPER_MODEL': ('whisper', 'model'),
    'DICTATION_AUDIO_DEVICE': ('audio', 'device'),
    'DICTATION_TYPING_DELAY': ('text', 'typing_delay'),
    # ... etc
}
```

#### 3.3 Dictation Module (`dictate.py`)

**Purpose**: Core functionality - audio recording, transcription, text injection.

**Key Functions:**

**`record_audio()`**
- Uses `sounddevice` library (PortAudio backend)
- Records at 16kHz mono (Whisper requirement)
- Saves to temporary WAV file
- Handles SIGTERM gracefully (sets cleanup flag)
- Returns path to audio file

**`transcribe_audio()`**
- Uses `faster-whisper` for optimized inference
- Loads model from cache (first run downloads from Hugging Face)
- Applies configuration: model, device, compute_type, beam_size, etc.
- Processes audio with VAD filter (removes silence)
- Returns transcribed text

**`inject_text()`**
- Uses `xdotool` to simulate keyboard input
- Respects typing_delay setting (prevents missed characters)
- Applies text processing: capitalize, strip spaces, etc.
- Fallback to clipboard if xdotool fails

**`notify()`**
- Uses `notify-send` or `dunstify`
- Shows status notifications (Recording started, Transcription complete, Errors)
- Configurable urgency and timeout

**Signal Handling:**
- `SIGTERM` sets global flag `_cleanup_requested = True`
- Recording loop checks flag and exits cleanly
- Temporary files are cleaned up properly
- Prevents SIGTERM hang issue (see Story 10)

## Data Flow

### Start Recording Flow

```
1. User presses Ctrl+'
2. XFCE invokes dictation-toggle.sh --toggle
3. Script checks /tmp/dictation.lock
4. Lock file doesn't exist → START mode
5. Script creates lock file with PID
6. Script invokes: uv run dictation-toggle --start
7. UV checks environment (auto-sync if needed)
8. Python module loads configuration
9. Python starts audio recording
10. Notification: "Recording started..."
11. Script exits (recording continues in background)
```

### Stop Recording Flow

```
1. User presses Ctrl+' again
2. XFCE invokes dictation-toggle.sh --toggle
3. Script checks /tmp/dictation.lock
4. Lock file exists → STOP mode
5. Script reads PID from lock file
6. Script sends SIGTERM to recording process
7. Python receives SIGTERM, sets cleanup flag
8. Recording loop exits gracefully
9. Audio file saved to /tmp/dictation/*.wav
10. Python transcribes audio with Whisper
11. Python injects text via xdotool
12. Python cleans up temporary files
13. Script removes lock file
14. Notification: "Transcription complete: [text preview]"
```

### Error Handling Flow

```
Error occurs during recording/transcription
    ↓
Python logs error to /tmp/dictation-toggle.log
    ↓
Python sends error notification
    ↓
Python cleans up resources (files, lock)
    ↓
Exit with non-zero status
    ↓
Shell script detects error
    ↓
Shell script cleans up lock file
    ↓
Notification: "Dictation failed: [error]"
```

## Configuration System

### Configuration Precedence

**Priority order (highest to lowest):**

1. **Environment Variables** - Temporary overrides, good for testing
   ```bash
   DICTATION_WHISPER_MODEL=tiny.en uv run dictation-toggle --start
   ```

2. **TOML File** - Persistent user configuration
   ```toml
   # ~/.config/automation-scripts/dictation.toml
   [whisper]
   model = "base.en"
   ```

3. **Built-in Defaults** - Sensible defaults for all settings
   ```python
   DEFAULT_WHISPER_MODEL = 'base.en'
   DEFAULT_COMPUTE_TYPE = 'int8'
   ```

### Configuration Loading Process

```
1. Start with DEFAULT_CONFIG (from constants.py)
2. Check if TOML file exists (~/.config/automation-scripts/dictation.toml)
3. If exists: Parse TOML and merge with defaults
4. Scan environment for DICTATION_* variables
5. Apply environment overrides (type conversion)
6. Validate complete configuration
7. Raise ConfigurationError if validation fails
8. Return final configuration dictionary
```

### Configuration Sections

**`[whisper]`** - Speech recognition settings
- `model` - Model size (tiny.en to large)
- `device` - cpu, cuda, auto
- `compute_type` - int8, int16, float16, float32
- `language` - ISO 639-1 code (en, es, fr, etc.)
- `beam_size` - Search breadth (1-10)
- `temperature` - Sampling randomness (0.0 = deterministic)
- `vad_filter` - Voice activity detection (true/false)

**`[audio]`** - Recording settings
- `device` - Microphone name or "default"
- `sample_rate` - Must be 16000 for Whisper
- `channels` - Must be 1 (mono) for Whisper

**`[text]`** - Text injection settings
- `paste_method` - xdotool, clipboard, both
- `typing_delay` - Milliseconds between keystrokes
- `auto_capitalize` - Capitalize first letter
- `strip_spaces` - Remove leading/trailing whitespace
- `add_period` - Add period if missing

**`[notifications]`** - Desktop notifications
- `enable` - Show notifications (true/false)
- `tool` - notify-send or dunstify
- `urgency` - low, normal, critical
- `timeout` - Milliseconds (0 = default)
- `icon` - Icon name or path

**`[files]`** - File management
- `temp_dir` - Temporary audio file location
- `keep_temp_files` - Keep files after transcription
- `lock_file` - Lock file location

## Signal Handling

### The SIGTERM Hang Problem (Story 10)

**Problem**: Earlier versions hung when receiving SIGTERM during recording, blocking indefinitely in the audio processing loop.

**Root Cause**: `sounddevice` blocking I/O with no timeout mechanism.

**Solution**: Flag-based cleanup with periodic checks.

**Implementation:**

```python
# Global flag checked by recording loop
_cleanup_requested = False

def signal_handler(signum, frame):
    """Set cleanup flag without blocking."""
    global _cleanup_requested
    _cleanup_requested = True
    
# Register handler
signal.signal(signal.SIGTERM, signal_handler)

# Recording loop checks flag
while recording:
    if _cleanup_requested:
        break  # Exit cleanly
    # Process audio chunk
```

**Why this works:**
- No blocking in signal handler (unsafe)
- Recording loop maintains control
- Clean shutdown with resource cleanup
- Works with sounddevice's callback mechanism

### Signal Flow

```
SIGTERM received
    ↓
signal_handler() sets _cleanup_requested = True
    ↓
Recording callback sees flag on next iteration
    ↓
Callback stops accepting new audio
    ↓
Recording function exits loop
    ↓
Cleanup: Close file, remove lock, send notification
    ↓
Process exits with status 0 (clean shutdown)
```

## UV Environment Management

### Auto-Sync on First Run (Story 10.5)

**Problem**: First run after boot could fail if UV environment wasn't synced.

**Solution**: Auto-detect and sync environment before invoking Python module.

**Implementation** (in `dictation-toggle.sh`):

```bash
# Check if UV environment exists and is synced
if ! uv run python -c "import automation_scripts.dictation" 2>/dev/null; then
    echo "UV environment needs sync, running uv sync..."
    uv sync --extra dictation
fi
```

**When this triggers:**
- First run after boot (new shell)
- After `uv.lock` file changes (dependencies updated)
- After repository checkout (new workspace)

**Performance**: UV sync is fast (< 5 seconds typical).

### UV Benefits

**Speed**: 
- 10-100x faster than pip for dependency resolution
- Instant environment creation (no virtualenv overhead)
- Parallel downloads and installs

**Reliability**:
- Lock file (`uv.lock`) ensures reproducible builds
- Conflict detection before installation
- Atomic operations (no partial installs)

**Developer Experience**:
- Single command: `uv sync --extra dictation`
- No virtualenv activation needed
- Automatic Python version management

## Systemd Integration

### Service Design

**Type: oneshot**
- Service runs once and exits
- `RemainAfterExit=yes` keeps it in "active" state
- Allows `systemctl reload` to re-register hotkey

**ExecStart**: `/home/user/.local/bin/register-hotkey.sh`
- Absolute path (no $PATH assumptions)
- Idempotent (can be run multiple times safely)
- Uses `xfconf-query` to set XFCE keyboard shortcut

**ExecReload**: `killall -HUP xfce4-settings-helper`
- SIGHUP tells XFCE to reload keyboard shortcuts
- Necessary for changes to take effect immediately

**Dependencies**:
- `After=xfce4-session.target` - Wait for XFCE to start
- `WantedBy=default.target` - Start on user login

### Service Lifecycle

```
User logs in
    ↓
systemd starts default.target
    ↓
dictation-hotkey.service starts
    ↓
register-hotkey.sh writes to xfconf
    ↓
SIGHUP sent to xfce4-settings-helper
    ↓
Hotkey is now active
    ↓
Service enters "active" state (remains after exit)
    ↓
User can press Ctrl+' to dictate
```

### Diagnostic Tool

**File**: `scripts/check-hotkey-status.sh`

**Purpose**: Comprehensive health check for the dictation system.

**Checks performed:**
1. Systemd service status (active/enabled)
2. Hotkey registration in XFCE settings
3. UV environment health (can import module)
4. Recent logs from dictation-toggle.log
5. Process status (any recordings in progress)

**Output format**:
```
=== Dictation Hotkey Status ===

[✓] Systemd service: active
[✓] Hotkey registered: Ctrl+'
[✓] UV environment: healthy
[✓] Python module: importable

Recent logs (last 10 lines):
[timestamp] Recording started
[timestamp] Transcription complete: hello world

No issues detected!
```

## Design Decisions

### Why TOML for Configuration?

**Alternatives considered**: JSON, YAML, INI

**Chosen**: TOML

**Reasons**:
- Human-readable and easy to edit
- Built-in Python support (tomllib in 3.11+)
- Strong typing (strings, integers, booleans, arrays)
- Comments supported
- Standard for Python projects (pyproject.toml)

### Why XDG Base Directory Specification?

**Alternatives**: Single config file in repo, home directory clutter

**Chosen**: XDG

**Reasons**:
- Standard Linux directory structure
- Separates config (backed up) from cache (disposable)
- Respects user's environment preferences
- Clean, organized directory structure

### Why Lock Files for State Management?

**Alternatives**: PID files, shared memory, database

**Chosen**: Lock files

**Reasons**:
- Simple and reliable
- No external dependencies
- Works across process boundaries
- Easy to debug (just `cat /tmp/dictation.lock`)
- Standard Unix pattern

### Why Systemd Service for Hotkey?

**Alternatives**: Autostart entry, login script, cron @reboot

**Chosen**: Systemd user service

**Reasons**:
- Reliable startup (waits for desktop environment)
- Proper dependency management (After= directive)
- Easy status checking (systemctl status)
- Logging (journalctl)
- Standard Linux service management

### Why Shell Script Wrapper?

**Alternatives**: Pure Python CLI, desktop automation tool

**Chosen**: Shell script

**Reasons**:
- Simple state management (lock files)
- Easy hotkey integration
- Minimal overhead
- Transparent (user can read and modify)
- Handles environment activation

### Why faster-whisper Instead of openai-whisper?

**Alternatives**: OpenAI's official whisper, other inference engines

**Chosen**: faster-whisper

**Reasons**:
- 4x faster inference with CTranslate2
- Lower memory usage
- Better quantization support (int8)
- Same model quality
- Active maintenance

## Performance Characteristics

### Cold Start (First Run After Boot)

```
UV environment sync: ~5 seconds
Model download (base.en): ~30 seconds (one-time)
Model loading: ~2 seconds
Total: ~37 seconds (subsequent: ~7 seconds)
```

### Warm Start (Model Cached)

```
Configuration loading: <0.1 seconds
Audio recording: Real-time (10 seconds of speech = 10 seconds)
Transcription (base.en, CPU): ~2-5 seconds for 10s audio
Text injection: <0.5 seconds
Total: ~12-15 seconds for 10s recording
```

### Memory Usage

```
Python process (idle): ~50 MB
Model loaded (base.en): ~2 GB
During transcription: ~2.5 GB peak
After completion: ~50 MB (model unloaded)
```

### Disk Usage

```
UV environment: ~500 MB
base.en model: ~140 MB
Temporary audio file: ~1 MB per minute
Logs: ~1-10 MB typical
```

## Future Improvements

### Potential Enhancements

1. **Wayland Support**: Use alternative to xdotool (wtype, ydotool)
2. **GPU Acceleration**: Automatic CUDA detection and usage
3. **VAD Auto-Stop**: Automatically stop recording when silence detected
4. **Real-Time Transcription**: Show partial results as user speaks
5. **Custom Vocabularies**: Add specialized terms for better accuracy
6. **Multi-Language Support**: Automatic language detection
7. **Punctuation Model**: Better automatic punctuation
8. **Integration APIs**: REST API for other applications

### Known Limitations

1. **X11 Only**: Wayland not yet supported (xdotool limitation)
2. **Single Recording**: Can't record multiple sources simultaneously
3. **No Streaming**: Must finish recording before transcription starts
4. **CPU-Bound**: Transcription uses 100% CPU during processing
5. **English-Focused**: .en models optimize for English only

## Testing Architecture

See [tests/README.md](../tests/README.md) for complete testing documentation.

**Test Organization**:
- Unit tests: Configuration, validation, path handling
- Integration tests: Audio, transcription, text injection (manual only)
- Fixtures: Mock XDG paths, sample configs, environment overrides

**Coverage**: >70% for core modules (config.py, constants.py)

---

This architecture document is maintained as part of the project's technical documentation. For implementation details, see the source code. For user-facing documentation, see the README and user guides.

