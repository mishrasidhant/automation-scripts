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

# Export ALL configuration variables for dictate.py
export DICTATION_WHISPER_MODEL="${DICTATION_WHISPER_MODEL:-base.en}"
export DICTATION_WHISPER_DEVICE="${DICTATION_WHISPER_DEVICE:-cpu}"
export DICTATION_WHISPER_COMPUTE_TYPE="${DICTATION_WHISPER_COMPUTE_TYPE:-int8}"
export DICTATION_WHISPER_LANGUAGE="${DICTATION_WHISPER_LANGUAGE:-en}"
export DICTATION_WHISPER_BEAM_SIZE="${DICTATION_WHISPER_BEAM_SIZE:-5}"
export DICTATION_WHISPER_TEMPERATURE="${DICTATION_WHISPER_TEMPERATURE:-0.0}"
export DICTATION_WHISPER_VAD_FILTER="${DICTATION_WHISPER_VAD_FILTER:-true}"
export DICTATION_WHISPER_INITIAL_PROMPT="${DICTATION_WHISPER_INITIAL_PROMPT:-}"

export DICTATION_AUDIO_DEVICE="${DICTATION_AUDIO_DEVICE:-}"
export DICTATION_SAMPLE_RATE="${DICTATION_SAMPLE_RATE:-16000}"
export DICTATION_CHANNELS="${DICTATION_CHANNELS:-1}"

export DICTATION_PASTE_METHOD="${DICTATION_PASTE_METHOD:-xdotool}"
export DICTATION_TYPING_DELAY="${DICTATION_TYPING_DELAY:-12}"
export DICTATION_CLEAR_MODIFIERS="${DICTATION_CLEAR_MODIFIERS:-true}"
export DICTATION_STRIP_LEADING_SPACE="${DICTATION_STRIP_LEADING_SPACE:-true}"
export DICTATION_STRIP_TRAILING_SPACE="${DICTATION_STRIP_TRAILING_SPACE:-true}"
export DICTATION_AUTO_CAPITALIZE="${DICTATION_AUTO_CAPITALIZE:-false}"
export DICTATION_AUTO_PUNCTUATION="${DICTATION_AUTO_PUNCTUATION:-true}"
export DICTATION_TEXT_REPLACEMENTS="${DICTATION_TEXT_REPLACEMENTS:-}"

export DICTATION_ENABLE_NOTIFICATIONS="${DICTATION_ENABLE_NOTIFICATIONS:-true}"
export DICTATION_NOTIFICATION_TOOL="${DICTATION_NOTIFICATION_TOOL:-notify-send}"
export DICTATION_NOTIFICATION_URGENCY="${DICTATION_NOTIFICATION_URGENCY:-normal}"
export DICTATION_NOTIFICATION_TIMEOUT="${DICTATION_NOTIFICATION_TIMEOUT:-3000}"
export DICTATION_SHOW_TRANSCRIPTION_IN_NOTIFICATION="${DICTATION_SHOW_TRANSCRIPTION_IN_NOTIFICATION:-true}"

export DICTATION_TEMP_DIR="${DICTATION_TEMP_DIR:-/tmp/dictation}"
export DICTATION_KEEP_TEMP_FILES="${DICTATION_KEEP_TEMP_FILES:-false}"
export DICTATION_LOCK_FILE="${DICTATION_LOCK_FILE:-/tmp/dictation.lock}"
export DICTATION_LOG_FILE="${DICTATION_LOG_FILE:-}"
export DICTATION_LOG_LEVEL="${DICTATION_LOG_LEVEL:-INFO}"

export DICTATION_DEBUG="${DICTATION_DEBUG:-false}"

# Call dictate.py with toggle mode
python3 "$DICTATE_PY" --toggle

# Exit with dictate.py's exit code
exit $?

