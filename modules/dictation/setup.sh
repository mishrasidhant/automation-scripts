#!/bin/bash
#
# Dictation Module Setup Script
# Automated installation and configuration for Manjaro + XFCE
#
# Usage: ./setup.sh [--yes] [--no-hotkey] [--skip-tests]
#
# Options:
#   --yes          Non-interactive mode (auto-accept all prompts)
#   --no-hotkey    Skip XFCE hotkey registration
#   --skip-tests   Skip validation tests
#

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
NONINTERACTIVE=false
SKIP_HOTKEY=false
SKIP_TESTS=false

# Arrays to track missing dependencies
MISSING_DEPS=()

# Exit codes
EXIT_SUCCESS=0
EXIT_MISSING_DEPS=1
EXIT_INSTALL_FAILED=2
EXIT_TESTS_FAILED=3
EXIT_MISSING_TOOLS=10

# ============================================================================
# === ARGUMENT PARSING ===
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --yes|-y)
            NONINTERACTIVE=true
            shift
            ;;
        --no-hotkey)
            SKIP_HOTKEY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --yes, -y       Non-interactive mode (auto-accept all prompts)"
            echo "  --no-hotkey     Skip XFCE hotkey registration"
            echo "  --skip-tests    Skip validation tests"
            echo "  --help, -h      Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# === HELPER FUNCTIONS ===
# ============================================================================

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Pretty print with status
print_status() {
    local status=$1
    local message=$2
    case $status in
        success) echo -e "${GREEN}✓${NC} $message" ;;
        error)   echo -e "${RED}✗${NC} $message" ;;
        warning) echo -e "${YELLOW}⚠${NC} $message" ;;
        info)    echo -e "${BLUE}ℹ${NC} $message" ;;
    esac
}

# Print section header
print_header() {
    echo ""
    echo "$1"
    echo "$(printf '=%.0s' $(seq 1 ${#1}))"
}

# ============================================================================
# === SYSTEM DEPENDENCY CHECKS ===
# ============================================================================

# Check system dependency
check_system_dep() {
    local dep=$1
    local package=${2:-$dep}  # Package name may differ from command
    
    if command_exists "$dep"; then
        print_status success "$dep is installed"
        return 0
    else
        print_status error "$dep is not installed"
        MISSING_DEPS+=("$package")
        return 1
    fi
}

# Check all system dependencies
check_system_dependencies() {
    print_header "Checking system dependencies..."
    
    # Essential tools
    check_system_dep "python3"
    check_system_dep "pip"
    
    # Dictation-specific dependencies
    check_system_dep "xdotool"
    check_system_dep "notify-send" "libnotify"
    
    # Note: portaudio is a C library required by sounddevice (Python package)
    # We don't check for it here because there's no single command to test
    # If sounddevice fails to import, the Python dependency check will catch it
    
    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        echo ""
        print_status info "All system dependencies are satisfied"
        return 0
    else
        return 1
    fi
}

# ============================================================================
# === PYTHON ENVIRONMENT SETUP ===
# ============================================================================

# Install system dependencies
install_system_deps() {
    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        return 0
    fi
    
    echo ""
    echo "The following system packages need to be installed:"
    printf '  - %s\n' "${MISSING_DEPS[@]}"
    
    if ! $NONINTERACTIVE; then
        echo ""
        read -p "Install now with pacman? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status warning "Skipping system package installation"
            return 1
        fi
    fi
    
    echo ""
    print_status info "Installing system packages..."
    sudo pacman -S --needed --noconfirm "${MISSING_DEPS[@]}"
    
    if [ $? -eq 0 ]; then
        print_status success "System dependencies installed"
        return 0
    else
        print_status error "Failed to install system dependencies"
        return 1
    fi
}

# Setup Python virtual environment and install dependencies
setup_python_environment() {
    print_header "Setting up Python environment..."
    
    local requirements_file="$PROJECT_ROOT/requirements/dictation.txt"
    
    # Check if requirements file exists
    if [ ! -f "$requirements_file" ]; then
        print_status error "Requirements file not found: $requirements_file"
        return 1
    fi
    
    # Create venv if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo ""
        print_status info "Creating project virtual environment..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            print_status error "Failed to create virtual environment"
            return 1
        fi
        print_status success "Virtual environment created"
        
        # Upgrade pip in new venv
        print_status info "Upgrading pip..."
        "$VENV_PIP" install --upgrade pip > /dev/null 2>&1
    else
        print_status info "Virtual environment already exists"
    fi
    
    # Always attempt to install/update dependencies
    echo ""
    echo "Will install Python dependencies from: requirements/dictation.txt"
    echo "Into: $VENV_DIR"
    
    if ! $NONINTERACTIVE; then
        echo ""
        read -p "Install/update dependencies? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status warning "Skipping Python dependency installation"
            echo "  Note: Validation tests may fail if dependencies are not installed"
            return 0
        fi
    fi
    
    echo ""
    print_status info "Installing Python dependencies..."
    "$VENV_PIP" install -r "$requirements_file"
    
    if [ $? -eq 0 ]; then
        print_status success "Python dependencies installed successfully"
        return 0
    else
        print_status error "Failed to install Python dependencies"
        return 1
    fi
}

# ============================================================================
# === DIRECTORY AND FILE SETUP ===
# ============================================================================

# Create required directories
create_directories() {
    print_header "Creating directories..."
    
    local dirs=(
        "/tmp/dictation"
        "$HOME/.local/share/dictation"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_status success "Created $dir"
            else
                print_status error "Failed to create $dir"
                return 1
            fi
        else
            print_status info "$dir already exists"
        fi
    done
    
    return 0
}

# Set executable permissions
set_permissions() {
    print_header "Setting permissions..."
    
    local files=(
        "${SCRIPT_DIR}/dictation-toggle.sh"
        "${SCRIPT_DIR}/dictate.py"
    )
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            print_status error "$file not found"
            return 1
        fi
        
        chmod +x "$file" 2>/dev/null
        if [ $? -eq 0 ] && [ -x "$file" ]; then
            print_status success "$(basename "$file") is executable"
        else
            print_status error "Failed to make $(basename "$file") executable"
            return 1
        fi
    done
    
    return 0
}

# ============================================================================
# === XFCE HOTKEY REGISTRATION ===
# ============================================================================

# Register XFCE hotkey
register_hotkey() {
    if $SKIP_HOTKEY; then
        print_status info "Skipping hotkey registration (--no-hotkey flag)"
        return 0
    fi
    
    print_header "XFCE Hotkey Registration"
    
    local default_hotkey="<Primary>apostrophe"  # Ctrl+'
    local hotkey=$default_hotkey
    
    if ! $NONINTERACTIVE; then
        echo "Default hotkey: Ctrl+' (apostrophe)"
        read -p "Use default hotkey? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "Available modifiers: <Primary> (Ctrl), <Alt>, <Shift>, <Super>"
            echo "Example formats:"
            echo "  <Primary>apostrophe       -> Ctrl+'"
            echo "  <Primary><Alt>d           -> Ctrl+Alt+D"
            echo "  <Super>d                  -> Super+D"
            echo ""
            read -p "Enter custom hotkey: " hotkey
            if [ -z "$hotkey" ]; then
                hotkey=$default_hotkey
                print_status warning "Empty input, using default: $default_hotkey"
            fi
        fi
    fi
    
    local script_path="${SCRIPT_DIR}/dictation-toggle.sh"
    
    # Check if xfconf-query exists
    if ! command_exists "xfconf-query"; then
        print_status warning "xfconf-query not found (not running XFCE?)"
        echo "  Please register hotkey manually in your desktop environment"
        echo "  Command: $script_path"
        return 1
    fi
    
    echo ""
    print_status info "Registering hotkey..."
    xfconf-query -c xfce4-keyboard-shortcuts \
        -p "/commands/custom/$hotkey" \
        -n -t string \
        -s "$script_path" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        local display_hotkey="${hotkey//<Primary>/Ctrl}"
        display_hotkey="${display_hotkey//<Alt>/Alt}"
        display_hotkey="${display_hotkey//<Shift>/Shift}"
        display_hotkey="${display_hotkey//<Super>/Super}"
        display_hotkey="${display_hotkey//apostrophe/\'}"
        print_status success "Hotkey registered: $display_hotkey"
        return 0
    else
        print_status warning "Could not register hotkey automatically"
        echo "  Please register manually in XFCE Settings → Keyboard → Application Shortcuts"
        echo "  Command: $script_path"
        echo "  Hotkey: ${hotkey//<Primary>/Ctrl}"
        return 1
    fi
}

# ============================================================================
# === VALIDATION TESTS ===
# ============================================================================

# Test audio device availability
test_audio_device() {
    print_status info "Testing audio device availability..."
    
    # Use venv Python
    local python_cmd="$VENV_PYTHON"
    if [ ! -f "$python_cmd" ]; then
        python_cmd="python3"
    fi
    
    local output=$($python_cmd -c "
import sounddevice as sd
devices = sd.query_devices()
input_devices = [d for d in devices if d['max_input_channels'] > 0]
if input_devices:
    print('Found {} input device(s):'.format(len(input_devices)))
    for d in input_devices[:3]:  # Show max 3
        print('  - {}'.format(d['name']))
    exit(0)
else:
    print('ERROR: No audio input devices found')
    exit(1)
" 2>&1)
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "$output" | while IFS= read -r line; do
            echo "    $line"
        done
        print_status success "Audio input device(s) available"
        return 0
    else
        print_status error "No audio input devices found"
        echo "    Make sure a microphone is connected"
        return 1
    fi
}

# Test Whisper model loading
test_whisper_model() {
    print_status info "Testing Whisper model (this may download ~145MB on first run)..."
    
    # Use venv Python
    local python_cmd="$VENV_PYTHON"
    if [ ! -f "$python_cmd" ]; then
        python_cmd="python3"
    fi
    
    local output=$(timeout 90 $python_cmd -c "
from faster_whisper import WhisperModel
import sys
try:
    model = WhisperModel('base.en', device='cpu', compute_type='int8')
    print('Whisper model loaded successfully')
    sys.exit(0)
except Exception as e:
    print(f'Error loading model: {e}')
    sys.exit(1)
" 2>&1)
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_status success "Whisper model loaded successfully"
        return 0
    elif [ $exit_code -eq 124 ]; then
        print_status error "Whisper model loading timed out (90s)"
        echo "    This might be due to slow network. Try running setup again."
        return 1
    else
        print_status error "Failed to load Whisper model"
        echo "    $output"
        return 1
    fi
}

# Test xdotool functionality
test_xdotool() {
    print_status info "Testing xdotool functionality..."
    
    # Detect display server
    local display_server="Unknown"
    if [ -n "$WAYLAND_DISPLAY" ]; then
        display_server="Wayland"
    elif [ -n "$DISPLAY" ]; then
        display_server="X11"
    fi
    
    if xdotool getactivewindow &> /dev/null; then
        print_status success "xdotool is working (running on $display_server)"
        return 0
    else
        if [ "$display_server" = "Wayland" ]; then
            print_status error "xdotool requires X11 - currently running on Wayland"
            echo "    The dictation module does NOT support Wayland"
            echo "    Please log out and select an X11/Xorg session to use this module"
        else
            print_status warning "xdotool test failed (display server: $display_server)"
            echo "    This might indicate a configuration issue"
        fi
        return 1
    fi
}

# Run all validation tests
run_validation_tests() {
    if $SKIP_TESTS; then
        print_status info "Skipping validation tests (--skip-tests flag)"
        return 0
    fi
    
    print_header "Running validation tests..."
    
    local test_results=0
    
    test_audio_device
    test_results=$((test_results + $?))
    
    echo ""
    test_whisper_model
    test_results=$((test_results + $?))
    
    echo ""
    test_xdotool
    local xdotool_result=$?
    
    # Detect if we're on Wayland - this IS a critical issue
    if [ $xdotool_result -ne 0 ] && [ -n "$WAYLAND_DISPLAY" ]; then
        echo ""
        print_status error "CRITICAL: Dictation module requires X11"
        echo ""
        echo "Current session: Wayland (not supported)"
        echo "Action required: Log out and select an X11/Xorg session"
        test_results=$((test_results + 1))  # Count as failure
    elif [ $xdotool_result -ne 0 ]; then
        # Failed but not on Wayland - might be other issue, don't block setup
        print_status warning "xdotool test failed but not running Wayland - investigate"
    fi
    
    return $test_results
}

# ============================================================================
# === MAIN SETUP FLOW ===
# ============================================================================

main() {
    # Print banner
    clear
    print_header "Dictation Module Setup"
    echo "Automated installation and configuration for Manjaro + XFCE"
    echo ""
    
    # Check for essential tools
    local missing_tools=()
    if ! command_exists "pacman"; then
        missing_tools+=("pacman (required for Manjaro/Arch Linux)")
    fi
    if ! command_exists "python3"; then
        missing_tools+=("python3")
    fi
    if ! command_exists "pip"; then
        missing_tools+=("pip (python-pip)")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_status error "The following required tools are missing:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        exit $EXIT_MISSING_TOOLS
    fi
    
    # Step 1: Check system dependencies
    check_system_dependencies
    local sys_check=$?
    
    # Step 2: Install missing system dependencies
    if [ $sys_check -ne 0 ]; then
        install_system_deps
        if [ $? -ne 0 ]; then
            echo ""
            print_status error "Setup cannot continue without required system dependencies"
            exit $EXIT_INSTALL_FAILED
        fi
    fi
    
    # Step 3: Setup Python environment and install dependencies
    echo ""
    setup_python_environment
    if [ $? -ne 0 ]; then
        print_status warning "Python environment setup encountered errors"
        echo "  Continuing with remaining setup steps..."
    fi
    
    # Step 4: Create directories
    echo ""
    create_directories
    if [ $? -ne 0 ]; then
        print_status error "Failed to create required directories"
        exit $EXIT_INSTALL_FAILED
    fi
    
    # Step 5: Set permissions
    echo ""
    set_permissions
    if [ $? -ne 0 ]; then
        print_status error "Failed to set executable permissions"
        exit $EXIT_INSTALL_FAILED
    fi
    
    # Step 6: Register hotkey
    echo ""
    register_hotkey
    # Don't fail on hotkey registration issues (optional feature)
    
    # Step 7: Run validation tests
    echo ""
    run_validation_tests
    local test_result=$?
    
    # Final summary
    echo ""
    echo ""
    print_header "Setup Complete!"
    echo ""
    
    if [ $test_result -eq 0 ] || $SKIP_TESTS; then
        print_status success "The dictation module is ready to use"
    else
        print_status warning "Setup completed but some tests failed"
        echo "  The module may still work, but you should investigate the errors above"
    fi
    
    echo ""
    echo "Quick Start:"
    echo "  1. Press your configured hotkey (default: Ctrl+') to start recording"
    echo "  2. Speak your text"
    echo "  3. Press the hotkey again to stop and paste"
    echo ""
    echo "Virtual Environment:"
    if [ -d "$VENV_DIR" ]; then
        echo "  Location: $VENV_DIR"
        echo "  Activate: source $PROJECT_ROOT/scripts/setup-dev.sh dictation"
    fi
    echo ""
    echo "Configuration:"
    echo "  Edit: ${SCRIPT_DIR}/config/dictation.env"
    echo ""
    echo "Manual Testing:"
    echo "  ${SCRIPT_DIR}/dictation-toggle.sh"
    echo ""
    echo "For more information:"
    echo "  README: ${SCRIPT_DIR}/README.md"
    echo "  Requirements: ${PROJECT_ROOT}/requirements/dictation.txt"
    echo ""
    echo "Enjoy dictating!"
    echo ""
    
    if [ $test_result -eq 0 ] || $SKIP_TESTS; then
        exit $EXIT_SUCCESS
    else
        exit $EXIT_TESTS_FAILED
    fi
}

# Run main function
main

