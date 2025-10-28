#!/bin/bash
#
# Dictation Hotkey Unregistration Script
# Removes keyboard shortcut (Ctrl+') from XFCE configuration
#
# Purpose: Clean uninstallation of dictation hotkey
# Usage: ./scripts/unregister-hotkey.sh
#
# Requirements:
# - xfconf-query must be available
# - xfsettingsd should be running (optional, will attempt reload if available)
#
# Exit Codes:
#   0 = Success (hotkey removed or was already not registered)
#   1 = Error (xfconf-query failed)
#

set -euo pipefail

# Constants
HOTKEY="<Primary>apostrophe"
XFCONF_CHANNEL="xfce4-keyboard-shortcuts"
XFCONF_PROPERTY="/commands/custom/${HOTKEY}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Main script starts
log "Starting dictation hotkey unregistration"

# Validate xfconf-query is available
if ! command -v xfconf-query &> /dev/null; then
    log_error "xfconf-query command not found"
    log_error "Please install XFCE configuration tools (xfconf)"
    exit 1
fi

# Check if hotkey is currently registered
log "Checking current registration status..."
CURRENT_VALUE=$(xfconf-query -c "$XFCONF_CHANNEL" -p "$XFCONF_PROPERTY" 2>/dev/null || echo "")

if [ -z "$CURRENT_VALUE" ]; then
    log "Hotkey is not currently registered (already removed or never set)"
    log "Nothing to do."
    exit 0
fi

log "Current registration: $XFCONF_PROPERTY -> $CURRENT_VALUE"

# Remove hotkey registration
log "Removing hotkey registration..."
if xfconf-query -c "$XFCONF_CHANNEL" -p "$XFCONF_PROPERTY" -r 2>&1; then
    log "✓ Hotkey registration removed successfully"
else
    log_error "Failed to remove hotkey registration"
    log_error "This may indicate:"
    log_error "  - Property does not exist"
    log_error "  - Permissions issue with xfconf database"
    log_error "  - Corrupted XFCE configuration"
    exit 1
fi

# Verify removal
log "Verifying removal..."
VERIFY_VALUE=$(xfconf-query -c "$XFCONF_CHANNEL" -p "$XFCONF_PROPERTY" 2>/dev/null || echo "")

if [ -z "$VERIFY_VALUE" ]; then
    log "✓ Verification successful: hotkey removed"
else
    log_error "Verification failed: hotkey still registered as '$VERIFY_VALUE'"
    exit 1
fi

# Reload xfsettingsd if running (graceful reload)
log "Checking if xfsettingsd is running..."
if pgrep -x xfsettingsd > /dev/null 2>&1; then
    log "xfsettingsd is running, sending reload signal..."
    if pkill -HUP xfsettingsd; then
        log "✓ SIGHUP signal sent to xfsettingsd (graceful reload)"
    else
        log "Warning: Failed to send SIGHUP to xfsettingsd"
        log "The hotkey is removed but xfsettingsd may need manual restart"
        log "Manual command: pkill -HUP xfsettingsd"
    fi
else
    log "xfsettingsd is not running, no reload needed"
fi

# Final success message
log "=========================================="
log "✓ Hotkey unregistration completed successfully"
log "=========================================="
log "Removed: Ctrl+' (Primary+apostrophe)"
log "From: $XFCONF_CHANNEL:$XFCONF_PROPERTY"
log ""
log "The keyboard shortcut has been removed."
log ""
log "To verify: xfconf-query -c $XFCONF_CHANNEL -l | grep apostrophe"
log "(should return nothing)"

exit 0


