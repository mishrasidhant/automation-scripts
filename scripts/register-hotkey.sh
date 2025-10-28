#!/bin/bash
#
# Dictation Hotkey Registration Script
# Registers keyboard shortcut (Ctrl+') for dictation-toggle.sh
#
# Purpose: Run by systemd user service on login to ensure hotkey persistence
# Usage: Called by dictation-hotkey.service (systemd user service)
#
# Requirements:
# - xfsettingsd must be running (XFCE Settings Daemon)
# - xfconf-query must be available
# - dictation-toggle.sh must exist in project
#
# Exit Codes:
#   0 = Success (hotkey registered and xfsettingsd reloaded)
#   1 = General error (xfconf-query failed, verification failed)
#   2 = Timeout error (xfsettingsd not available within 30s)
#

set -euo pipefail

# Constants
HOTKEY="<Primary>apostrophe"
XFCONF_CHANNEL="xfce4-keyboard-shortcuts"
XFCONF_PROPERTY="/commands/custom/${HOTKEY}"
TIMEOUT_SECONDS=30

# Detect project root (resolve symlinks for robust detection)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOGGLE_SCRIPT="${PROJECT_ROOT}/scripts/dictation-toggle.sh"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Main script starts
log "Starting dictation hotkey registration"
log "Project root: $PROJECT_ROOT"
log "Toggle script: $TOGGLE_SCRIPT"

# Validate toggle script exists
if [ ! -f "$TOGGLE_SCRIPT" ]; then
    log_error "Toggle script not found at: $TOGGLE_SCRIPT"
    log_error "Please ensure dictation-toggle.sh exists in scripts/ directory"
    exit 1
fi

# Validate toggle script is executable
if [ ! -x "$TOGGLE_SCRIPT" ]; then
    log "Warning: Toggle script not executable, setting permissions..."
    chmod +x "$TOGGLE_SCRIPT" 2>/dev/null || {
        log_error "Failed to set executable permission on toggle script"
        exit 1
    }
fi

# Wait for xfsettingsd availability (max 30 seconds)
log "Waiting for xfsettingsd to become available (timeout: ${TIMEOUT_SECONDS}s)..."
WAITED=0
while ! pgrep -x xfsettingsd > /dev/null 2>&1; do
    if [ $WAITED -ge $TIMEOUT_SECONDS ]; then
        log_error "xfsettingsd not available after ${TIMEOUT_SECONDS}s timeout"
        log_error "This may indicate:"
        log_error "  - XFCE desktop environment is not running"
        log_error "  - xfsettingsd service failed to start"
        log_error "  - System is not ready yet (try increasing timeout)"
        log_error ""
        log_error "Troubleshooting:"
        log_error "  1. Check if xfsettingsd is running: pgrep xfsettingsd"
        log_error "  2. Manually start: xfsettingsd &"
        log_error "  3. Check XFCE session: echo \$XDG_CURRENT_DESKTOP"
        exit 2
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done

log "xfsettingsd detected (waited ${WAITED}s)"

# Validate xfconf-query is available
if ! command -v xfconf-query &> /dev/null; then
    log_error "xfconf-query command not found"
    log_error "Please install XFCE configuration tools (xfconf)"
    exit 1
fi

# Register hotkey using xfconf-query
log "Registering hotkey: $HOTKEY -> $TOGGLE_SCRIPT"

if xfconf-query -c "$XFCONF_CHANNEL" \
    -p "$XFCONF_PROPERTY" \
    -n -t string \
    -s "$TOGGLE_SCRIPT" 2>&1; then
    log "xfconf-query command executed successfully"
else
    log_error "xfconf-query command failed"
    log_error "This may indicate:"
    log_error "  - XFCE configuration channel not accessible"
    log_error "  - Permissions issue with xfconf database"
    log_error "  - Corrupted XFCE configuration"
    log_error ""
    log_error "Troubleshooting:"
    log_error "  1. List channels: xfconf-query -l"
    log_error "  2. Check channel: xfconf-query -c $XFCONF_CHANNEL -l"
    log_error "  3. Reset config: mv ~/.config/xfce4/xfconf ~/xfconf.backup"
    exit 1
fi

# Verify registration by reading back the value
log "Verifying hotkey registration..."
REGISTERED_VALUE=$(xfconf-query -c "$XFCONF_CHANNEL" -p "$XFCONF_PROPERTY" 2>/dev/null || echo "")

if [ "$REGISTERED_VALUE" = "$TOGGLE_SCRIPT" ]; then
    log "✓ Verification successful: hotkey registered correctly"
else
    log_error "Verification failed!"
    log_error "Expected: $TOGGLE_SCRIPT"
    log_error "Got: $REGISTERED_VALUE"
    exit 1
fi

# Send SIGHUP to xfsettingsd to reload configuration
log "Reloading xfsettingsd configuration..."
if pkill -HUP xfsettingsd; then
    log "✓ SIGHUP signal sent to xfsettingsd (graceful reload)"
else
    log_error "Failed to send SIGHUP to xfsettingsd"
    log_error "The hotkey is registered but may not work until xfsettingsd restarts"
    log_error "Manual workaround: pkill -HUP xfsettingsd"
    exit 1
fi

# Final success message
log "=========================================="
log "✓ Hotkey registration completed successfully"
log "=========================================="
log "Hotkey: Ctrl+' (Primary+apostrophe)"
log "Command: $TOGGLE_SCRIPT"
log "Configuration: $XFCONF_CHANNEL:$XFCONF_PROPERTY"
log ""
log "You can now press Ctrl+' to toggle dictation"
log ""
log "To verify: xfconf-query -c $XFCONF_CHANNEL -p \"$XFCONF_PROPERTY\""
log "To check logs: journalctl --user -u dictation-hotkey.service"

exit 0


