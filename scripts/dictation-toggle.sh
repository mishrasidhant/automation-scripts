#!/bin/bash
#
# Dictation Toggle Wrapper Script (UV Migration)
# Triggers voice-to-text dictation via system hotkey
#
# Usage: Called automatically by XFCE keyboard shortcut (Ctrl+')
#
# This script has been updated to use UV for package management.
# Configuration is now loaded from ~/.config/automation-scripts/dictation.toml
# or via environment variables (DICTATION_*).
#

set -euo pipefail

# Determine script directory and project root
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root (required for UV to find pyproject.toml)
cd "$PROJECT_ROOT"

# Logging setup
LOG_FILE="/tmp/dictation-toggle.log"

log_message() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# Validate UV is available
if ! command -v uv &> /dev/null; then
    if command -v notify-send &> /dev/null; then
        notify-send -u critical "Dictation Error" "UV not found. Please install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    log_message "ERROR: UV not found in PATH"
    echo "ERROR: UV not found in PATH" >&2
    echo "Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# Validate pyproject.toml exists
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    if command -v notify-send &> /dev/null; then
        notify-send -u critical "Dictation Error" "pyproject.toml not found at $PROJECT_ROOT"
    fi
    log_message "ERROR: pyproject.toml not found at $PROJECT_ROOT"
    echo "ERROR: pyproject.toml not found at $PROJECT_ROOT" >&2
    exit 1
fi

# UV Environment Health Check Function
check_uv_environment() {
    log_message "INFO: Checking UV environment health..."
    
    # Check if .venv directory exists
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        log_message "WARN: .venv directory missing, triggering sync..."
        return 1
    fi
    
    # Check if uv.lock file exists
    if [ ! -f "$PROJECT_ROOT/uv.lock" ]; then
        log_message "WARN: uv.lock missing, triggering sync..."
        return 1
    fi
    
    # Quick validation: attempt to import Python
    if ! uv run python -c "import sys; sys.exit(0)" &>> "$LOG_FILE"; then
        log_message "WARN: UV environment validation failed, triggering sync..."
        return 1
    fi
    
    log_message "INFO: UV environment healthy"
    return 0
}

# UV Environment Sync Function
sync_uv_environment() {
    log_message "INFO: Syncing UV environment..."
     
    if ! uv sync --extra dictation &>> "$LOG_FILE"; then
        log_message "ERROR: UV sync failed"
        if command -v notify-send &> /dev/null; then
            notify-send -u critical "Dictation Error" "UV sync failed. Check /tmp/dictation-toggle.log"
        fi
        return 1
    fi
    
    log_message "INFO: UV environment synced successfully"
    return 0
}

# Pre-flight check: Ensure UV environment is ready
log_message "INFO: Starting dictation toggle (pre-flight check)..."
if ! check_uv_environment; then
    # Show progress notification to user
    if command -v notify-send &> /dev/null; then
        notify-send -t 3000 "Dictation" "Initializing environment, please wait..." &
    fi
    if ! sync_uv_environment; then
        log_message "ERROR: Failed to prepare UV environment, aborting"
        exit 1
    fi
fi

# Optional: Export environment variables for configuration overrides
# These override TOML configuration if set
# Examples:
#   export DICTATION_WHISPER_MODEL=tiny.en
#   export DICTATION_AUDIO_DEVICE=hw:0
#   export DICTATION_TYPING_DELAY=20

# Legacy .env file support (deprecated but supported for migration period)
LEGACY_CONFIG="${PROJECT_ROOT}/modules/dictation/config/dictation.env"
if [ -f "$LEGACY_CONFIG" ]; then
    # Source the legacy config but don't export all variables
    # Let the Python config system handle TOML as the primary source
    source "$LEGACY_CONFIG" 2>/dev/null || true
fi

# Execute dictation module with UV
# UV automatically activates the virtual environment and uses locked dependencies
log_message "INFO: Launching dictation module..."
exec uv run -m automation_scripts.dictation --toggle

# Note: exec replaces the shell process, so exit code is from dictation module


