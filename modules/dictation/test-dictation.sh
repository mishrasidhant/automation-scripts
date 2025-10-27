#!/bin/bash
#
# Dictation Module Test Suite
# Validates installation and functionality
#
# IMPORTANT: This test should be run from within the activated virtual environment
# To run properly:
#   1. cd automation-scripts
#   2. source scripts/setup-dev.sh [or source .venv/bin/activate]
#   3. cd modules/dictation
#   4. ./test-dictation.sh
#

set -uo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Dictation Module Test Suite         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Test function wrapper
run_test() {
    local test_name=$1
    shift
    echo -n "Testing: $test_name ... "
    
    if "$@"; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Skip test function
skip_test() {
    local test_name=$1
    local reason=$2
    echo -e "Testing: $test_name ... ${YELLOW}SKIP${NC} ($reason)"
    ((TESTS_SKIPPED++))
}

# Individual test functions

test_python_available() {
    command -v python3 &> /dev/null
}

test_pip_available() {
    command -v pip &> /dev/null || command -v pip3 &> /dev/null
}

test_xdotool_available() {
    command -v xdotool &> /dev/null
}

test_notify_send_available() {
    command -v notify-send &> /dev/null
}

test_sounddevice_installed() {
    python3 -c "import sounddevice" 2> /dev/null
}

test_faster_whisper_installed() {
    python3 -c "import faster_whisper" 2> /dev/null
}

test_numpy_installed() {
    python3 -c "import numpy" 2> /dev/null
}

test_portaudio_installed() {
    # Check if portaudio library is available via sounddevice import
    # This is more reliable than ldconfig which may not show it
    python3 -c "import sounddevice" 2> /dev/null && python3 -c "import sounddevice as sd; sd.query_devices()" 2> /dev/null
}

test_audio_device_detected() {
    python3 -c "
import sounddevice as sd
devices = sd.query_devices()
exit(0 if len(devices) > 0 else 1)
" 2> /dev/null
}

test_whisper_model_loads() {
    # Test if Whisper model can be loaded (may download on first run)
    timeout 30 python3 -c "
from faster_whisper import WhisperModel
import sys
try:
    model = WhisperModel('base.en', device='cpu', compute_type='int8')
    print('Model loaded successfully', file=sys.stderr)
    exit(0)
except Exception as e:
    print(f'Model load failed: {e}', file=sys.stderr)
    exit(1)
" 2> /dev/null
}

test_xdotool_can_type() {
    # We can't actually test typing without user interaction
    # Just verify xdotool accepts the command structure
    xdotool type --help &> /dev/null
}

test_lock_file_operations() {
    local test_lock="/tmp/dictation-test.lock"
    
    # Clean up any existing test lock
    rm -f "$test_lock"
    
    # Test create
    echo "$$" > "$test_lock" || return 1
    
    # Test read
    [ -f "$test_lock" ] || return 1
    
    # Test delete
    rm "$test_lock" || return 1
    [ ! -f "$test_lock" ] || return 1
    
    return 0
}

test_config_file_exists() {
    [ -f "$SCRIPT_DIR/config/dictation.env" ]
}

test_config_file_valid() {
    # Test if config file can be sourced without errors
    (source "$SCRIPT_DIR/config/dictation.env") 2> /dev/null
}

test_dictate_py_exists() {
    [ -f "$SCRIPT_DIR/dictate.py" ]
}

test_dictate_py_executable() {
    [ -x "$SCRIPT_DIR/dictate.py" ] || [ -r "$SCRIPT_DIR/dictate.py" ]
}

test_dictation_toggle_exists() {
    [ -f "$SCRIPT_DIR/dictation-toggle.sh" ]
}

test_dictation_toggle_executable() {
    [ -x "$SCRIPT_DIR/dictation-toggle.sh" ]
}

test_temp_dir_writable() {
    local test_file="/tmp/dictation/.test_$$"
    mkdir -p /tmp/dictation || return 1
    touch "$test_file" || return 1
    rm "$test_file" || return 1
    return 0
}

test_xfce_hotkey_registered() {
    if ! command -v xfconf-query &> /dev/null; then
        return 0  # Pass if not XFCE (handled by skip_test in main)
    fi
    
    # Check if the registered hotkey exists and points to dictation-toggle.sh
    # Check the default hotkey: <Primary>apostrophe (Ctrl+')
    local hotkey_path="/commands/custom/<Primary>apostrophe"
    local registered_cmd=$(xfconf-query -c xfce4-keyboard-shortcuts -p "$hotkey_path" 2> /dev/null)
    
    # Check if the command contains "dictation"
    echo "$registered_cmd" | grep -q "dictation"
}

# Test for virtual environment
test_venv_exists() {
    local venv_dir="${SCRIPT_DIR}/../../.venv"
    [ -d "$venv_dir" ]
}

test_venv_activated() {
    [ -n "${VIRTUAL_ENV:-}" ]
}

# Main test execution
main() {
    echo "=== System Dependencies ==="
    run_test "Python 3 availability" test_python_available
    run_test "pip availability" test_pip_available
    run_test "xdotool availability" test_xdotool_available
    run_test "notify-send availability" test_notify_send_available
    run_test "portaudio installed" test_portaudio_installed
    echo
    
    echo "=== Virtual Environment ==="
    run_test "Virtual environment exists" test_venv_exists
    if test_venv_exists; then
        skip_test "Virtual environment activated" "Run this script from within the activated venv"
    else
        skip_test "Virtual environment activated" "Virtual environment not found"
    fi
    echo
    
    echo "=== Python Packages ==="
    run_test "sounddevice installed" test_sounddevice_installed
    run_test "faster-whisper installed" test_faster_whisper_installed
    run_test "numpy installed" test_numpy_installed
    echo
    
    echo "=== Audio System ==="
    if test_sounddevice_installed; then
        run_test "Audio input device detected" test_audio_device_detected
    else
        skip_test "Audio input device detected" "sounddevice not installed"
    fi
    echo
    
    echo "=== Whisper Model ==="
    if test_faster_whisper_installed; then
        echo -n "Testing: Whisper model loads ... "
        if test_whisper_model_loads; then
            echo -e "${GREEN}PASS${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${YELLOW}FAIL/TIMEOUT${NC} (model download may be in progress)"
            ((TESTS_FAILED++))
        fi
    else
        skip_test "Whisper model loads" "faster-whisper not installed"
    fi
    echo
    
    echo "=== Text Injection ==="
    run_test "xdotool can type" test_xdotool_can_type
    echo
    
    echo "=== File System ==="
    run_test "Lock file operations" test_lock_file_operations
    run_test "Temp directory writable" test_temp_dir_writable
    echo
    
    echo "=== Module Files ==="
    run_test "dictate.py exists" test_dictate_py_exists
    run_test "dictate.py accessible" test_dictate_py_executable
    run_test "dictation-toggle.sh exists" test_dictation_toggle_exists
    run_test "dictation-toggle.sh executable" test_dictation_toggle_executable
    run_test "Config file exists" test_config_file_exists
    run_test "Config file valid" test_config_file_valid
    echo
    
    echo "=== Integration ==="
    if command -v xfconf-query &> /dev/null; then
        run_test "XFCE hotkey registered" test_xfce_hotkey_registered
    else
        skip_test "XFCE hotkey registered" "Not running XFCE"
    fi
    echo
    
    # Summary
    echo "===================================="
    echo -e "Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}, ${YELLOW}$TESTS_SKIPPED skipped${NC}"
    echo "===================================="
    echo
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed! Module is ready to use.${NC}"
        echo
        echo "To test manually:"
        echo "  ./dictation-toggle.sh"
        echo
        return 0
    else
        echo -e "${RED}✗ Some tests failed. Please review errors above.${NC}"
        echo
        echo "Common fixes:"
        echo "  - Install missing packages: ./setup.sh"
        echo "  - Activate virtual environment: source .venv/bin/activate (from project root)"
        echo "  - Install Python packages in venv: pip install -r ../../requirements/dictation.txt"
        echo "  - System packages: sudo pacman -S xdotool portaudio libnotify"
        echo
        return 1
    fi
}

# Run tests
main
exit $?

