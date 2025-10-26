# Dictation Module - Audio Recording

Core audio recording functionality for the dictation system.

## Overview

This module provides command-line audio recording capabilities using Python's sounddevice library. It's designed to work with the system's default microphone and saves recordings in WAV format optimized for speech recognition.

## Features

- ✅ CLI-based audio recording control (`--start`, `--stop`)
- ✅ Lock file state management to prevent concurrent recordings
- ✅ Desktop notifications for user feedback
- ✅ Automatic audio device detection
- ✅ WAV file creation optimized for Whisper transcription (16kHz, mono)
- ✅ Error handling for common audio issues
- ✅ No root/sudo privileges required

## Prerequisites

### System Dependencies

```bash
# Arch/Manjaro
sudo pacman -S portaudio xdotool libnotify

# Ubuntu/Debian (reference)
sudo apt-get install portaudio19-dev xdotool libnotify-bin
```

**See:** `docs/architecture/SYSTEM_DEPS.md` for complete system requirements.

### Python Dependencies

Managed via project virtual environment. See `requirements/dictation.txt` for details.

**Dependencies:**
- sounddevice >= 0.4.6 (audio I/O)
- numpy >= 1.24.0 (audio data processing)

**See:** `docs/architecture/dependency-management.md` for architecture details.

**Note:** The script will check for dependencies on startup and show helpful error messages if anything is missing.

## Installation

### Quick Setup

```bash
# 1. Install system dependencies
sudo pacman -S portaudio xdotool libnotify

# 2. From project root, setup virtual environment and install Python dependencies
cd $AUTOMATION_SCRIPTS_DIR
source scripts/setup-dev.sh dictation

# 3. Verify installation
python -c "import sounddevice; print('✓ sounddevice')"
python -c "import numpy; print('✓ numpy')"
```

### Manual Setup (Alternative)

```bash
# 1. Install system dependencies (as above)

# 2. Create and activate virtual environment
cd $AUTOMATION_SCRIPTS_DIR
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements/dictation.txt

# 4. Verify
cd modules/dictation
python test_dictate.py
```

**Note:** The script is already executable. Virtual environment is required for dependencies.

## Usage

**Important:** Activate the virtual environment before running commands.

```bash
# From project root
source .venv/bin/activate
# Or use the helper script
source scripts/setup-dev.sh
```

### Start Recording

```bash
# With venv activated
cd modules/dictation
python dictate.py --start

# Or with absolute path and venv Python
/path/to/.venv/bin/python modules/dictation/dictate.py --start
```

This will:
- Check audio device availability
- Create `/tmp/dictation/` directory if needed
- Create a lock file at `/tmp/dictation.lock`
- Begin recording audio from the default microphone
- Show a desktop notification
- Keep running until stopped

### Stop Recording

In a separate terminal (or after pressing Ctrl+C):

```bash
python3 dictate.py --stop
```

This will:
- Stop the audio recording
- Save the audio to a WAV file in `/tmp/dictation/`
- Remove the lock file
- Show a desktop notification with recording duration

### Help

```bash
python3 dictate.py --help
```

## File Locations

- **Lock File:** `/tmp/dictation.lock`
- **Audio Files:** `/tmp/dictation/recording-<PID>-<timestamp>.wav`

## Lock File Format

The lock file contains JSON with recording metadata:

```json
{
  "pid": 12345,
  "started_at": 1729900000,
  "audio_file": "/tmp/dictation/recording-12345-1729900000.wav",
  "stream_info": {
    "device": "Blue Microphones",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

## Audio Specifications

- **Format:** WAV (PCM)
- **Sample Rate:** 16000 Hz (optimized for Whisper)
- **Channels:** 1 (mono)
- **Bit Depth:** 16-bit signed integer
- **Device:** System default input (auto-detected)

## Error Handling

The script handles common issues gracefully:

- **No audio device:** Shows error with device listing
- **Recording already in progress:** Prevents duplicate recordings
- **Stale lock files:** Automatically cleaned up
- **Missing dependencies:** Shows installation instructions
- **Disk space issues:** Reports errors clearly

## Testing

Run the unit tests:

```bash
python3 test_dictate.py
```

Tests cover:
- Lock file management
- Process detection
- CLI argument parsing
- Notifications
- Error handling
- Audio configuration

## Manual Testing

### Basic Recording Test

```bash
# Start recording
python3 dictate.py --start

# Speak for a few seconds
# (In another terminal)

# Stop recording
python3 dictate.py --stop

# Verify file exists and can be played
ls -lh /tmp/dictation/
aplay /tmp/dictation/recording-*.wav
```

### Multiple Recordings Test

```bash
# Record 3 separate sessions
for i in {1..3}; do
  python3 dictate.py --start
  sleep 2
  python3 dictate.py --stop
  sleep 1
done

# Verify 3 files exist
ls -lh /tmp/dictation/
```

### Lock File Test

```bash
# Start recording
python3 dictate.py --start &

# Try to start again (should fail)
python3 dictate.py --start
# Expected: "Error: Recording already in progress"

# Stop
python3 dictate.py --stop
```

## Troubleshooting

### "No module named 'sounddevice'"

Install the Python package:
```bash
pip install sounddevice
```

### "Audio device error"

Check available devices:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Verify PulseAudio is running:
```bash
pulseaudio --check
echo $?  # Should output 0 if running
```

### "Permission denied" on /tmp

Check `/tmp` permissions:
```bash
ls -ld /tmp
# Should be: drwxrwxrwt
```

### No desktop notifications

Check if notify-send is installed:
```bash
which notify-send
```

Install if missing:
```bash
# Arch/Manjaro
sudo pacman -S libnotify

# Ubuntu/Debian
sudo apt-get install libnotify-bin
```

## Integration

This module is designed to be the foundation for:
- **Story 2:** Speech transcription (reads WAV files)
- **Story 3:** Text injection (triggered after recording)
- **Story 4:** Hotkey wrapper (calls this script)

## Architecture

For detailed architecture information, see:
- `docs/DICTATION_ARCHITECTURE.md`
- `docs/stories/story-1-audio-recording.md`

## License

Part of the systemd-automations project.

## Author

Sidhant Dixit

## Version

1.0.0 - Initial implementation (Story 1 / DICT-001)

