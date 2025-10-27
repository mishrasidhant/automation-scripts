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

