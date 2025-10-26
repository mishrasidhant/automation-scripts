# System Dependencies

**Version:** 1.0  
**Date:** October 26, 2025  
**Platform:** Arch Linux / Manjaro

---

## Overview

This document lists all system-level dependencies required by automation modules in this project. These packages must be installed via the system package manager (`pacman`) and cannot be installed in the Python virtual environment.

---

## Installation Summary

```bash
# All modules (complete installation)
sudo pacman -S portaudio xdotool libnotify

# Or install per module as needed (see below)
```

---

## Dependencies by Module

### Dictation Module

**Required:**
- `portaudio` - Audio I/O library for sounddevice
- `xdotool` - X11 automation for text injection
- `libnotify` - Desktop notifications (notify-send)

**Installation:**
```bash
sudo pacman -S portaudio xdotool libnotify
```

**Verification:**
```bash
pacman -Q portaudio xdotool libnotify
ldconfig -p | grep portaudio
which xdotool notify-send
```

**Why These Are System Packages:**
- `portaudio` - C library with hardware drivers
- `xdotool` - Binary executable for X11
- `libnotify` - System notification daemon integration

---

### Backup Module (Future)

**Required:**
- `rsync` - File synchronization utility
- `borgbackup` - Deduplicating backup tool

**Installation:**
```bash
sudo pacman -S rsync borgbackup
```

---

### Monitoring Module (Future)

**Required:**
- None (pure Python)

**Optional:**
- `smartmontools` - Disk health monitoring
- `lm_sensors` - Hardware sensors

---

## Python Dependencies

**Note:** Python package dependencies are managed separately via virtual environment.

See: `requirements/` directory and `docs/architecture/dependency-management.md`

Python packages (installed via pip in venv):
- sounddevice (Python bindings for portaudio)
- numpy
- faster-whisper
- etc.

---

## Troubleshooting

### portaudio Not Found

**Symptom:**
```python
import sounddevice
# ImportError: libportaudio.so.2: cannot open shared object file
```

**Solution:**
```bash
sudo pacman -S portaudio
# Verify
ldconfig -p | grep portaudio
```

---

### xdotool Command Not Found

**Symptom:**
```bash
xdotool type "test"
# bash: xdotool: command not found
```

**Solution:**
```bash
sudo pacman -S xdotool
which xdotool  # Should show /usr/bin/xdotool
```

---

### notify-send Not Working

**Symptom:**
- No desktop notifications appear
- Command runs but nothing shows

**Solution:**
```bash
# Check if libnotify is installed
pacman -Q libnotify

# Test notification manually
notify-send "Test" "This is a test"

# Check if notification daemon is running
ps aux | grep -i notif

# XFCE uses xfce4-notifyd
systemctl --user status xfce4-notifyd.service
```

---

## Checking Installed System Dependencies

```bash
# Create verification script
cat > scripts/verify-system-deps.sh << 'EOF'
#!/bin/bash
echo "Checking system dependencies..."

DEPS="portaudio xdotool libnotify"
MISSING=""

for dep in $DEPS; do
    if pacman -Q $dep &>/dev/null; then
        echo "✓ $dep"
    else
        echo "✗ $dep (missing)"
        MISSING="$MISSING $dep"
    fi
done

if [ -n "$MISSING" ]; then
    echo ""
    echo "Install missing dependencies:"
    echo "  sudo pacman -S$MISSING"
    exit 1
else
    echo ""
    echo "All system dependencies installed!"
    exit 0
fi
EOF

chmod +x scripts/verify-system-deps.sh
./scripts/verify-system-deps.sh
```

---

## Platform-Specific Notes

### Arch Linux / Manjaro
- Use `pacman` package manager
- Packages are up-to-date
- AUR may have additional packages via `yay`

### Ubuntu / Debian (Reference)
If porting to Debian-based systems:
```bash
# Equivalent packages
sudo apt-get install portaudio19-dev libxdo-dev libnotify-bin
```

### Fedora (Reference)
```bash
sudo dnf install portaudio-devel xdotool libnotify
```

---

## Keeping System Dependencies Updated

```bash
# Update all system packages (including dependencies)
sudo pacman -Syu

# Check for updates to specific package
pacman -Qu | grep portaudio
```

---

## Adding New System Dependencies

**Process:**

1. Determine if dependency is needed:
   - Can it be a Python package? → Use venv
   - Is it a C library or binary? → System package

2. Add to this document:
   - List under appropriate module
   - Document why it's a system package
   - Provide installation command

3. Update verification script:
   - Add to DEPS list in verify-system-deps.sh

4. Update module README:
   - Note system dependency in prerequisites

---

## Why Not Use Python Packages for These?

### portaudio
- **Why system package:** C library with hardware drivers
- **Python alternative:** None (sounddevice is just bindings)
- **Could use pip:** No, sounddevice requires system libportaudio

### xdotool
- **Why system package:** Standalone binary for X11
- **Python alternative:** python-xlib (less reliable)
- **Could use pip:** Not recommended, xdotool is standard tool

### libnotify
- **Why system package:** Integrates with system notification daemon
- **Python alternative:** notify2 (pip package, but less reliable)
- **Could use pip:** Yes, but system package is better

**General Rule:** If it interfaces with hardware or system services, use system package.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-26 | Winston | Initial documentation |

