# Story 5: Automated Setup Script with Dependency Validation

**Story ID:** DICT-005  
**Epic:** Dictation Module Implementation  
**Priority:** Medium (Quality of Life)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 hours  
**Depends On:** Story 4 (Complete module structure)

---

## User Story

**As a** new user or system administrator,  
**I want** an automated setup script that validates and installs all dependencies,  
**So that** I can get the dictation module working quickly without manual configuration.

---

## Story Context

### Existing System Integration

- **Builds on:** Complete dictation module (Stories 1-4)
- **Technology:** Bash script, pacman/yay (Manjaro), pip (Python)
- **Target:** Manjaro Linux + XFCE setup
- **Follows pattern:** Interactive setup scripts with validation

### Technical Approach

Create comprehensive setup automation:
- Validate system dependencies (xdotool, portaudio, notify-send)
- Install missing system packages via pacman
- Validate Python dependencies (sounddevice, faster-whisper)
- Install missing Python packages via pip
- Create required directories
- Set executable permissions
- Offer to register XFCE hotkey
- Run validation tests
- Provide user-friendly output and error handling

---

## Acceptance Criteria

### Functional Requirements

1. **Setup script validates all system dependencies**
   - Checks for: xdotool, portaudio, notify-send, python3, pip
   - Reports which dependencies are present/missing
   - Offers to install missing dependencies automatically

2. **Setup script validates all Python dependencies**
   - Checks for: sounddevice, faster-whisper, numpy
   - Reports version information for installed packages
   - Offers to install missing packages automatically

3. **Setup script creates required directory structure**
   - Creates: `/tmp/dictation/` (if not exists)
   - Creates: `~/.local/share/dictation/` (for logs, optional)
   - Sets appropriate permissions

### Integration Requirements

4. **Setup script configures file permissions**
   - Makes `dictation-toggle.sh` executable (755)
   - Makes `dictate.py` executable (755)
   - Validates permissions after setting

5. **Setup script offers XFCE hotkey registration**
   - Prompts user for hotkey preference (default: Ctrl+')
   - Registers hotkey via xfconf-query
   - Validates registration was successful
   - Can be skipped (manual registration)

6. **Setup script runs validation tests**
   - Tests audio device availability
   - Tests whisper model loading (downloads if needed)
   - Tests xdotool availability
   - Optionally runs end-to-end test

### Quality Requirements

7. **Setup is user-friendly and informative**
   - Clear progress indicators at each stage
   - Color-coded output (green=success, red=error, yellow=warning)
   - Helpful error messages with resolution steps
   - Non-interactive mode available (--yes flag)

8. **Setup is idempotent (safe to re-run)**
   - Doesn't reinstall if already present
   - Doesn't overwrite user configuration
   - Can be used to validate existing installation
   - Provides "repair" functionality

9. **Setup handles errors gracefully**
   - Doesn't fail catastrophically on single error
   - Provides clear next steps on failure
   - Can be partially completed and resumed
   - Logs errors for debugging

---

## Technical Implementation Details

### File Structure (Final)

```
modules/dictation/
├── README.md                    # User docs (Story 6)
├── dictate.py                   # Core script (Stories 1-3)
├── dictation-toggle.sh          # Wrapper script (Story 4)
├── setup.sh                     # Setup script (this story) ← NEW
└── config/
    └── dictation.env            # Configuration (Story 4)
```

### setup.sh Structure

```bash
#!/bin/bash
#
# Dictation Module Setup Script
# Automated installation and configuration for Manjaro + XFCE
#
# Usage: ./setup.sh [--yes] [--no-hotkey] [--skip-tests]
#

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NONINTERACTIVE=false
SKIP_HOTKEY=false
SKIP_TESTS=false

# === Parse Arguments ===
# === Helper Functions ===
# === System Dependency Checks ===
# === Python Dependency Checks ===
# === Directory Creation ===
# === Permission Setting ===
# === XFCE Hotkey Registration ===
# === Validation Tests ===
# === Main Setup Flow ===
```

### Key Functions

```bash
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

# Check Python package
check_python_package() {
    local package=$1
    
    if python3 -c "import $package" &> /dev/null; then
        local version=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")
        print_status success "$package is installed (version: $version)"
        return 0
    else
        print_status error "$package is not installed"
        MISSING_PY_PACKAGES+=("$package")
        return 1
    fi
}

# Install system dependencies
install_system_deps() {
    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        print_status info "All system dependencies are satisfied"
        return 0
    fi
    
    echo ""
    echo "The following system packages need to be installed:"
    printf '  - %s\n' "${MISSING_DEPS[@]}"
    
    if ! $NONINTERACTIVE; then
        read -p "Install now with pacman? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status warning "Skipping system package installation"
            return 1
        fi
    fi
    
    sudo pacman -S --needed --noconfirm "${MISSING_DEPS[@]}"
    
    if [ $? -eq 0 ]; then
        print_status success "System dependencies installed"
        return 0
    else
        print_status error "Failed to install system dependencies"
        return 1
    fi
}

# Install Python packages
install_python_packages() {
    if [ ${#MISSING_PY_PACKAGES[@]} -eq 0 ]; then
        print_status info "All Python dependencies are satisfied"
        return 0
    fi
    
    echo ""
    echo "The following Python packages need to be installed:"
    printf '  - %s\n' "${MISSING_PY_PACKAGES[@]}"
    
    if ! $NONINTERACTIVE; then
        read -p "Install now with pip? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status warning "Skipping Python package installation"
            return 1
        fi
    fi
    
    pip install --user "${MISSING_PY_PACKAGES[@]}"
    
    if [ $? -eq 0 ]; then
        print_status success "Python dependencies installed"
        return 0
    else
        print_status error "Failed to install Python dependencies"
        return 1
    fi
}

# Register XFCE hotkey
register_hotkey() {
    if $SKIP_HOTKEY; then
        print_status info "Skipping hotkey registration (--no-hotkey flag)"
        return 0
    fi
    
    echo ""
    echo "XFCE Hotkey Registration"
    echo "========================"
    
    local default_hotkey="<Primary>apostrophe"  # Ctrl+'
    local hotkey=$default_hotkey
    
    if ! $NONINTERACTIVE; then
        echo "Default hotkey: Ctrl+' (apostrophe)"
        read -p "Use default hotkey? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Available modifiers: <Primary> (Ctrl), <Alt>, <Shift>, <Super>"
            read -p "Enter custom hotkey (e.g., <Primary><Alt>d): " hotkey
        fi
    fi
    
    local script_path="${SCRIPT_DIR}/dictation-toggle.sh"
    
    xfconf-query -c xfce4-keyboard-shortcuts \
        -p "/commands/custom/$hotkey" \
        -n -t string \
        -s "$script_path" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status success "Hotkey registered: ${hotkey//<Primary>/Ctrl}"
        return 0
    else
        print_status warning "Could not register hotkey automatically"
        echo "  Please register manually in XFCE Settings → Keyboard → Application Shortcuts"
        echo "  Command: $script_path"
        return 1
    fi
}

# Validation test: Audio device
test_audio_device() {
    print_status info "Testing audio device availability..."
    
    python3 -c "
import sounddevice as sd
devices = sd.query_devices()
input_devices = [d for d in devices if d['max_input_channels'] > 0]
if input_devices:
    print('Found {} input device(s):'.format(len(input_devices)))
    for d in input_devices:
        print('  - {}'.format(d['name']))
    exit(0)
else:
    print('ERROR: No audio input devices found')
    exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status success "Audio input device(s) available"
        return 0
    else
        print_status error "No audio input devices found"
        return 1
    fi
}

# Validation test: Whisper model
test_whisper_model() {
    print_status info "Testing Whisper model (this may download ~145MB on first run)..."
    
    timeout 60 python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('base.en', device='cpu', compute_type='int8')
print('Whisper model loaded successfully')
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status success "Whisper model loaded successfully"
        return 0
    else
        print_status error "Failed to load Whisper model"
        return 1
    fi
}
```

---

## Implementation Checklist

### Phase 1: Script Structure & Argument Parsing
- [ ] Create `setup.sh` file
- [ ] Add shebang and header documentation
- [ ] Parse command-line arguments (--yes, --no-hotkey, --skip-tests)
- [ ] Define color codes and helper functions

### Phase 2: Dependency Validation
- [ ] Implement system dependency checks
- [ ] Implement Python dependency checks
- [ ] Create arrays to track missing dependencies
- [ ] Report current status

### Phase 3: Dependency Installation
- [ ] Implement system package installation (pacman)
- [ ] Implement Python package installation (pip)
- [ ] Add user confirmation prompts
- [ ] Handle installation errors

### Phase 4: File System Setup
- [ ] Create `/tmp/dictation/` directory
- [ ] Create `~/.local/share/dictation/` directory
- [ ] Set executable permissions on scripts
- [ ] Validate directory structure

### Phase 5: XFCE Hotkey Registration
- [ ] Prompt for hotkey preference
- [ ] Register via xfconf-query
- [ ] Validate registration
- [ ] Provide manual instructions as fallback

### Phase 6: Validation Tests
- [ ] Test audio device availability
- [ ] Test Whisper model loading
- [ ] Test xdotool functionality
- [ ] Optional: end-to-end test

### Phase 7: Error Handling & Reporting
- [ ] Collect all validation results
- [ ] Generate summary report
- [ ] Provide next steps on failures
- [ ] Exit with appropriate code

---

## Testing Strategy

### Manual Tests

1. **Fresh Installation Test**
   ```bash
   # Clean system (uninstall dependencies first for testing)
   pip uninstall -y sounddevice faster-whisper
   sudo pacman -R xdotool
   
   # Run setup
   cd modules/dictation
   ./setup.sh
   
   # Follow prompts, verify:
   # - Dependencies installed
   # - Hotkey registered
   # - Tests pass
   ```

2. **Non-Interactive Mode Test**
   ```bash
   ./setup.sh --yes
   # Should auto-install everything without prompts
   ```

3. **Idempotence Test**
   ```bash
   ./setup.sh
   # First run: installs dependencies
   
   ./setup.sh
   # Second run: should detect everything is installed, skip
   ```

4. **Partial Setup Test**
   ```bash
   ./setup.sh --no-hotkey --skip-tests
   # Should install dependencies but skip hotkey and tests
   ```

5. **Repair Mode Test**
   ```bash
   # Break permissions
   chmod 644 dictation-toggle.sh
   
   # Run setup
   ./setup.sh
   
   # Should detect and fix permissions
   ```

---

## Definition of Done

- ✅ Setup script exists and is executable
- ✅ Validates all system dependencies
- ✅ Validates all Python dependencies
- ✅ Installs missing dependencies automatically
- ✅ Creates required directories
- ✅ Sets correct file permissions
- ✅ Offers XFCE hotkey registration
- ✅ Runs validation tests
- ✅ Provides clear user feedback
- ✅ Is idempotent (safe to re-run)
- ✅ Handles errors gracefully
- ✅ Manual tests pass

---

## Dependencies

### Script Requirements
- bash (already present ✓)
- pacman (already present ✓)
- xfconf-query (already present ✓)
- sudo (for package installation)

### Dependencies to Install (if missing)
- System: xdotool, portaudio, libnotify
- Python: sounddevice, faster-whisper

### No New Dependencies
All tools needed for setup script are already on the system.

---

## Example Usage (After Implementation)

```bash
# Interactive installation
$ cd $HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation
$ ./setup.sh

Dictation Module Setup
======================

Checking system dependencies...
✓ python3 is installed
✓ pip is installed
✓ notify-send is installed
✗ xdotool is not installed
✗ portaudio is not installed

The following system packages need to be installed:
  - xdotool
  - portaudio

Install now with pacman? (y/n) y

[sudo] password for sdx: 
resolving dependencies...
✓ System dependencies installed

Checking Python dependencies...
✓ numpy is installed (version: 2.3.3)
✗ sounddevice is not installed
✗ faster-whisper is not installed

The following Python packages need to be installed:
  - sounddevice
  - faster-whisper

Install now with pip? (y/n) y

Collecting sounddevice...
✓ Python dependencies installed

Creating directories...
✓ Created /tmp/dictation/
✓ Created $HOME/.local/share/dictation/

Setting permissions...
✓ dictation-toggle.sh is executable
✓ dictate.py is executable

XFCE Hotkey Registration
========================
Default hotkey: Ctrl+' (apostrophe)
Use default hotkey? (y/n) y
✓ Hotkey registered: Ctrl+'

Running validation tests...
ℹ Testing audio device availability...
Found 2 input device(s):
  - HD-Audio Generic: ALC1220 Analog
  - Blue Microphones: USB Audio
✓ Audio input device(s) available

ℹ Testing Whisper model (this may download ~145MB on first run)...
Downloading model...
✓ Whisper model loaded successfully

========================================
Setup Complete! ✓
========================================

The dictation module is ready to use.

Quick Start:
  1. Press Ctrl+' to start recording
  2. Speak your text
  3. Press Ctrl+' again to stop and paste

Configuration:
  Edit: modules/dictation/config/dictation.env
  
To test manually:
  ./dictation-toggle.sh

Enjoy dictating!
```

---

## Success Metrics

- **Functionality:** All dependencies installed correctly
- **User Experience:** Clear progress and helpful messages
- **Reliability:** 100% success rate on clean system
- **Time:** Complete setup in <5 minutes
- **Idempotence:** Can be re-run safely

---

## Technical Notes

### Package Name Mapping

Some commands have different package names:

| Command | Manjaro Package |
|---------|----------------|
| notify-send | libnotify |
| xdotool | xdotool |
| portaudio | portaudio |

### Error Exit Codes

```bash
0  - Success
1  - Missing dependencies (not installed)
2  - Installation failed
3  - Validation tests failed
10 - Missing required tools (pacman, pip)
```

### Download Sizes

First-time setup will download:
- System packages: ~2-5 MB (xdotool, portaudio)
- Python packages: ~50 MB (sounddevice, faster-whisper)
- Whisper model: ~145 MB (base.en, auto-downloaded on first use)
- **Total: ~200 MB**

### Non-Interactive Mode

```bash
# For automation/scripting
./setup.sh --yes --no-hotkey --skip-tests

# Useful for:
# - Containerized environments
# - Automated deployment
# - CI/CD pipelines
```

---

## Risk Assessment

### Risks

1. **Package installation fails (network issue)**
   - **Mitigation:** Clear error message, retry instructions
   - **Likelihood:** Low

2. **pip install fails (permissions)**
   - **Mitigation:** Use --user flag, suggest pip install --user
   - **Likelihood:** Low (pip defaults to user install)

3. **XFCE hotkey registration fails**
   - **Mitigation:** Provide manual instructions
   - **Likelihood:** Low (xfconf-query is reliable)

4. **Whisper model download times out**
   - **Mitigation:** 60-second timeout, can retry later
   - **Likelihood:** Medium (large download)

### Rollback Plan

If setup fails:
```bash
# Uninstall Python packages
pip uninstall sounddevice faster-whisper

# Uninstall system packages (optional)
sudo pacman -R xdotool portaudio

# Remove hotkey
xfconf-query -c xfce4-keyboard-shortcuts \
  -p "/commands/custom/<Primary>apostrophe" -r

# Clean up directories
rm -rf /tmp/dictation/
rm -rf ~/.local/share/dictation/
```

---

## Future Enhancements

### Potential Additions
- `--uninstall` flag to remove everything
- `--update` flag to upgrade dependencies
- `--test-only` flag for validation without installation
- Support for other package managers (apt, dnf)
- Support for other desktop environments (GNOME, KDE)

### Model Management
```bash
./setup.sh --model tiny.en   # Install specific model
./setup.sh --model small.en  # Download larger model
```

---

## Related Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md` (Setup section)
- **Setup Checklist:** `docs/SETUP_CHECKLIST.md` (Manual steps reference)
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md` (Config file format)

---

**Story Status:** Ready for Implementation  
**Prerequisites:** Story 4 complete (all module files exist)  
**Blocks:** Story 6 (documentation should reference setup script)  
**Review Required:** Successful test on clean system before Story 6

