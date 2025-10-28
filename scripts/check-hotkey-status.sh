#!/bin/bash
#
# Dictation Hotkey Status Checker
# Comprehensive diagnostic tool for hotkey registration and service status
#
# Purpose: Troubleshoot hotkey persistence issues
# Usage: ./scripts/check-hotkey-status.sh
#
# Checks:
# - Systemd service status
# - xfconf registration
# - xfsettingsd daemon status
# - Recent service logs
# - Configuration files
#
# Exit Codes:
#   0 = All checks pass (hotkey system is healthy)
#   1 = One or more checks failed (issues detected)
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Constants
HOTKEY="<Primary>apostrophe"
XFCONF_CHANNEL="xfce4-keyboard-shortcuts"
XFCONF_PROPERTY="/commands/custom/${HOTKEY}"
SERVICE_NAME="dictation-hotkey.service"

# Status tracking
OVERALL_STATUS=0

# Logging functions
log_header() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo -e "$*"
    echo -e "==========================================${NC}"
}

log_success() {
    echo -e "  ${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "  ${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "  ${RED}✗${NC} $*"
    OVERALL_STATUS=1
}

log_info() {
    echo -e "  ${BLUE}ℹ${NC} $*"
}

# Main diagnostic starts
echo ""
echo "Dictation Hotkey Status Checker"
echo "================================="
echo ""

# Check 1: Systemd User Service Status
log_header "1. Systemd Service Status"

if ! command -v systemctl &> /dev/null; then
    log_error "systemctl command not found (systemd not installed)"
else
    if systemctl --user status > /dev/null 2>&1; then
        log_success "systemd user services available"
        
        # Check if service exists
        if systemctl --user list-unit-files "$SERVICE_NAME" | grep -q "$SERVICE_NAME"; then
            log_success "Service file installed: $SERVICE_NAME"
            
            # Check if enabled
            if systemctl --user is-enabled "$SERVICE_NAME" > /dev/null 2>&1; then
                log_success "Service enabled (will start on login)"
            else
                log_error "Service NOT enabled"
                log_info "Fix: systemctl --user enable $SERVICE_NAME"
            fi
            
            # Check if active
            if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
                log_success "Service active (running/completed)"
            else
                STATUS=$(systemctl --user is-active "$SERVICE_NAME" 2>&1 || echo "unknown")
                log_error "Service NOT active (status: $STATUS)"
                log_info "Fix: systemctl --user start $SERVICE_NAME"
            fi
            
            # Show detailed status
            echo ""
            echo "  Service Details:"
            systemctl --user status "$SERVICE_NAME" --no-pager -l 2>&1 | sed 's/^/    /' || true
            
        else
            log_error "Service file NOT installed"
            log_info "Fix: Run ./scripts/install-hotkey-service.sh"
        fi
    else
        log_error "systemd user services not running"
        log_info "Check: systemctl --user status"
    fi
fi

# Check 2: xfconf Registration
log_header "2. XFCE Hotkey Registration"

if ! command -v xfconf-query &> /dev/null; then
    log_error "xfconf-query command not found"
    log_info "Install: sudo apt install xfconf (Debian/Ubuntu)"
else
    log_success "xfconf-query available"
    
    # Check if channel exists
    if xfconf-query -l 2>&1 | grep -q "$XFCONF_CHANNEL"; then
        log_success "XFCE keyboard shortcuts channel exists"
        
        # Check if hotkey is registered
        HOTKEY_VALUE=$(xfconf-query -c "$XFCONF_CHANNEL" -p "$XFCONF_PROPERTY" 2>/dev/null || echo "")
        
        if [ -n "$HOTKEY_VALUE" ]; then
            log_success "Hotkey registered: Ctrl+' (Primary+apostrophe)"
            log_info "Command: $HOTKEY_VALUE"
            
            # Check if toggle script exists
            if [ -f "$HOTKEY_VALUE" ]; then
                log_success "Toggle script exists: $HOTKEY_VALUE"
                
                # Check if executable
                if [ -x "$HOTKEY_VALUE" ]; then
                    log_success "Toggle script is executable"
                else
                    log_error "Toggle script is NOT executable"
                    log_info "Fix: chmod +x $HOTKEY_VALUE"
                fi
            else
                log_error "Toggle script NOT found: $HOTKEY_VALUE"
                log_info "The hotkey points to a non-existent script"
            fi
        else
            log_error "Hotkey NOT registered in xfconf"
            log_info "Fix: Run ./scripts/register-hotkey.sh"
            log_info "Or: Run ./scripts/install-hotkey-service.sh"
        fi
    else
        log_error "XFCE keyboard shortcuts channel NOT found"
        log_info "This may indicate XFCE is not running or not configured"
    fi
fi

# Check 3: xfsettingsd Daemon
log_header "3. XFCE Settings Daemon (xfsettingsd)"

if pgrep -x xfsettingsd > /dev/null 2>&1; then
    PID=$(pgrep -x xfsettingsd)
    log_success "xfsettingsd is running (PID: $PID)"
    
    # Get process info
    if command -v ps &> /dev/null; then
        PROCESS_INFO=$(ps -p "$PID" -o cmd= 2>/dev/null || echo "")
        if [ -n "$PROCESS_INFO" ]; then
            log_info "Process: $PROCESS_INFO"
        fi
    fi
else
    log_error "xfsettingsd is NOT running"
    log_info "This is required for hotkeys to work"
    log_info "Fix (XFCE session should auto-start it):"
    log_info "  - Manual: xfsettingsd &"
    log_info "  - Check if XFCE is running: echo \$XDG_CURRENT_DESKTOP"
fi

# Check 4: Desktop Environment
log_header "4. Desktop Environment"

if [ -n "${XDG_CURRENT_DESKTOP:-}" ]; then
    log_info "Current desktop: $XDG_CURRENT_DESKTOP"
    
    if [[ "$XDG_CURRENT_DESKTOP" == *"XFCE"* ]]; then
        log_success "XFCE desktop detected"
    else
        log_warning "Non-XFCE desktop detected"
        log_info "This hotkey system requires XFCE"
    fi
else
    log_warning "XDG_CURRENT_DESKTOP not set"
    log_info "Desktop environment may not be properly configured"
fi

if [ -n "${XDG_SESSION_TYPE:-}" ]; then
    log_info "Session type: $XDG_SESSION_TYPE"
else
    log_warning "XDG_SESSION_TYPE not set"
fi

# Check 5: Service Logs
log_header "5. Recent Service Logs (Last 20 Lines)"

if command -v journalctl &> /dev/null; then
    if systemctl --user list-unit-files "$SERVICE_NAME" | grep -q "$SERVICE_NAME"; then
        echo ""
        journalctl --user -u "$SERVICE_NAME" -n 20 --no-pager 2>&1 | sed 's/^/  /' || {
            log_warning "No logs available yet (service may not have run)"
        }
    else
        log_info "Service not installed, no logs available"
    fi
else
    log_warning "journalctl not available (cannot view logs)"
fi

# Check 6: Configuration Files
log_header "6. Configuration Files"

SERVICE_FILE="${HOME}/.config/systemd/user/${SERVICE_NAME}"
REGISTER_SCRIPT="${HOME}/.local/bin/register-hotkey.sh"
UNREGISTER_SCRIPT="${HOME}/.local/bin/unregister-hotkey.sh"

if [ -f "$SERVICE_FILE" ]; then
    log_success "Service file exists: $SERVICE_FILE"
else
    log_error "Service file NOT found: $SERVICE_FILE"
    log_info "Fix: Run ./scripts/install-hotkey-service.sh"
fi

if [ -f "$REGISTER_SCRIPT" ]; then
    log_success "Registration script exists: $REGISTER_SCRIPT"
    
    if [ -x "$REGISTER_SCRIPT" ]; then
        log_success "Registration script is executable"
    else
        log_error "Registration script is NOT executable"
        log_info "Fix: chmod +x $REGISTER_SCRIPT"
    fi
else
    log_error "Registration script NOT found: $REGISTER_SCRIPT"
    log_info "Fix: Run ./scripts/install-hotkey-service.sh"
fi

if [ -f "$UNREGISTER_SCRIPT" ]; then
    log_success "Unregistration script exists: $UNREGISTER_SCRIPT"
else
    log_warning "Unregistration script NOT found: $UNREGISTER_SCRIPT"
fi

# Summary
log_header "Summary"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your hotkey registration system is healthy."
    echo "The keyboard shortcut (Ctrl+') should work and persist across reboots."
    echo ""
else
    echo -e "${RED}✗ Issues detected!${NC}"
    echo ""
    echo "Some checks failed. Review the output above for details."
    echo ""
    echo "Common fixes:"
    echo "  - Install service: ./scripts/install-hotkey-service.sh"
    echo "  - Register hotkey: ./scripts/register-hotkey.sh"
    echo "  - Start service: systemctl --user start $SERVICE_NAME"
    echo "  - Enable service: systemctl --user enable $SERVICE_NAME"
    echo "  - View logs: journalctl --user -u $SERVICE_NAME"
    echo ""
fi

echo "Additional Commands:"
echo "  - Test manually: ./scripts/register-hotkey.sh"
echo "  - Restart service: systemctl --user restart $SERVICE_NAME"
echo "  - View full logs: journalctl --user -u $SERVICE_NAME -b"
echo "  - Unregister: ./scripts/unregister-hotkey.sh"
echo ""

exit $OVERALL_STATUS


