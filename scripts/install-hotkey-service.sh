#!/bin/bash
#
# Dictation Hotkey Service Installation Script
# Installs systemd user service for automatic hotkey registration on login
#
# Purpose: One-command installation of hotkey persistence system
# Usage: ./scripts/install-hotkey-service.sh
#
# What it does:
# 1. Copies service file to ~/.config/systemd/user/
# 2. Copies registration/unregistration scripts to ~/.local/bin/
# 3. Sets executable permissions
# 4. Reloads systemd user daemon
# 5. Enables service (start on login)
# 6. Starts service immediately
# 7. Verifies installation success
#
# Exit Codes:
#   0 = Success (service installed and running)
#   1 = Error (installation failed)
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect project root
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source files
SERVICE_FILE="${PROJECT_ROOT}/systemd/dictation-hotkey.service"
REGISTER_SCRIPT="${PROJECT_ROOT}/scripts/register-hotkey.sh"
UNREGISTER_SCRIPT="${PROJECT_ROOT}/scripts/unregister-hotkey.sh"

# Destination locations
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
BIN_DIR="${HOME}/.local/bin"
SERVICE_DEST="${SYSTEMD_USER_DIR}/dictation-hotkey.service"
REGISTER_DEST="${BIN_DIR}/register-hotkey.sh"
UNREGISTER_DEST="${BIN_DIR}/unregister-hotkey.sh"

# Service name
SERVICE_NAME="dictation-hotkey.service"

# Logging functions
log() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_info() {
    echo -e "${YELLOW}[i]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

log_step() {
    echo ""
    echo "=========================================="
    echo "$*"
    echo "=========================================="
}

# Main script starts
log_step "Dictation Hotkey Service Installation"

# Check for systemd user support
log_info "Checking systemd user service support..."
if ! command -v systemctl &> /dev/null; then
    log_error "systemctl command not found"
    log_error "systemd is required for this installation"
    exit 1
fi

if ! systemctl --user status > /dev/null 2>&1; then
    log_error "systemd user services are not available"
    log_error "This may indicate systemd is not running in user mode"
    log_error "Try: systemctl --user status"
    exit 1
fi

log "systemd user services are available"

# Validate source files exist
log_info "Validating source files..."

if [ ! -f "$SERVICE_FILE" ]; then
    log_error "Service file not found: $SERVICE_FILE"
    exit 1
fi
log "Found service file: $SERVICE_FILE"

if [ ! -f "$REGISTER_SCRIPT" ]; then
    log_error "Registration script not found: $REGISTER_SCRIPT"
    exit 1
fi
log "Found registration script: $REGISTER_SCRIPT"

if [ ! -f "$UNREGISTER_SCRIPT" ]; then
    log_error "Unregistration script not found: $UNREGISTER_SCRIPT"
    exit 1
fi
log "Found unregistration script: $UNREGISTER_SCRIPT"

# Create destination directories
log_step "Creating Installation Directories"

log_info "Creating systemd user directory: $SYSTEMD_USER_DIR"
mkdir -p "$SYSTEMD_USER_DIR"
log "Created: $SYSTEMD_USER_DIR"

log_info "Creating bin directory: $BIN_DIR"
mkdir -p "$BIN_DIR"
log "Created: $BIN_DIR"

# Copy files
log_step "Copying Files"

log_info "Copying service file with project root path..."
# Customize service file with actual project root path
sed "s|%h/.local/bin/register-hotkey.sh|${PROJECT_ROOT}/scripts/register-hotkey.sh|g" "$SERVICE_FILE" > "$SERVICE_DEST"
log "Installed: $SERVICE_DEST (customized with project root)"

log_info "Copying registration script..."
cp "$REGISTER_SCRIPT" "$REGISTER_DEST"
log "Installed: $REGISTER_DEST"

log_info "Copying unregistration script..."
cp "$UNREGISTER_SCRIPT" "$UNREGISTER_DEST"
log "Installed: $UNREGISTER_DEST"

# Set executable permissions
log_step "Setting Permissions"

log_info "Setting executable permissions on scripts..."
chmod +x "$REGISTER_DEST"
log "Set executable: $REGISTER_DEST"

chmod +x "$UNREGISTER_DEST"
log "Set executable: $UNREGISTER_DEST"

# Reload systemd user daemon
log_step "Configuring Systemd"

log_info "Reloading systemd user daemon..."
if systemctl --user daemon-reload; then
    log "systemd user daemon reloaded"
else
    log_error "Failed to reload systemd user daemon"
    exit 1
fi

# Enable service
log_info "Enabling service (will start on login)..."
if systemctl --user enable "$SERVICE_NAME"; then
    log "Service enabled: $SERVICE_NAME"
else
    log_error "Failed to enable service"
    exit 1
fi

# Start service immediately
log_info "Starting service now..."
if systemctl --user start "$SERVICE_NAME"; then
    log "Service started: $SERVICE_NAME"
else
    log_error "Failed to start service"
    log_error "Check logs: journalctl --user -u $SERVICE_NAME"
    exit 1
fi

# Wait a moment for service to complete
sleep 2

# Verify service status
log_step "Verifying Installation"

log_info "Checking service status..."
if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
    log "Service is active"
else
    log_error "Service is not active"
    log_error "Status: $(systemctl --user is-active "$SERVICE_NAME")"
    log_error "Check logs: journalctl --user -u $SERVICE_NAME"
    exit 1
fi

if systemctl --user is-enabled "$SERVICE_NAME" > /dev/null 2>&1; then
    log "Service is enabled (will start on login)"
else
    log_error "Service is not enabled"
    exit 1
fi

# Display service logs
log_step "Service Logs (Last 10 Lines)"
echo ""
journalctl --user -u "$SERVICE_NAME" -n 10 --no-pager || true
echo ""

# Verify hotkey registration
log_step "Verifying Hotkey Registration"

log_info "Checking xfconf registration..."
HOTKEY_VALUE=$(xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe" 2>/dev/null || echo "")

if [ -n "$HOTKEY_VALUE" ]; then
    log "Hotkey registered: Ctrl+' -> $HOTKEY_VALUE"
else
    log_error "Hotkey not registered in xfconf"
    log_error "This may indicate the service encountered an error"
    log_error "Check logs: journalctl --user -u $SERVICE_NAME"
    exit 1
fi

# Success summary
log_step "Installation Complete!"

echo ""
echo "The dictation hotkey service has been successfully installed and started."
echo ""
echo -e "${GREEN}✓ Service Status:${NC} Active and enabled"
echo -e "${GREEN}✓ Hotkey:${NC} Ctrl+' (Primary+apostrophe)"
echo -e "${GREEN}✓ Command:${NC} $HOTKEY_VALUE"
echo ""
echo "Next Steps:"
echo "  1. Test the hotkey now: Press Ctrl+' to start dictation"
echo "  2. Reboot your system to verify persistence"
echo "  3. Check status anytime: systemctl --user status $SERVICE_NAME"
echo "  4. View logs: journalctl --user -u $SERVICE_NAME"
echo ""
echo "Troubleshooting:"
echo "  - Diagnostic: ./scripts/check-hotkey-status.sh"
echo "  - Unregister: ./scripts/unregister-hotkey.sh"
echo "  - Disable: systemctl --user disable $SERVICE_NAME"
echo "  - Stop: systemctl --user stop $SERVICE_NAME"
echo ""
echo "The hotkey will automatically register on every login from now on."
echo ""

exit 0

