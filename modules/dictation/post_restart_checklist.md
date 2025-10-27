# Post-Restart Testing Checklist for Dictation Module

## 1. Environment Validation (2 minutes)

### Check Virtual Environment
```bash
cd $HOME/Files/W/Workspace/git/automation-scripts
source .venv/bin/activate  # or: source scripts/setup-dev.sh dictation
```

### Verify Python Packages
```bash
python -c "import sounddevice; print('✓ sounddevice')"
python -c "import faster_whisper; print('✓ faster-whisper')"
python -c "import numpy; print('✓ numpy')"
```

### Check System Dependencies
```bash
which xdotool notify-send
python -c "import sounddevice as sd; sd.query_devices()"
```

### Verify Audio Device (Critical)
```bash
# Your Blue Microphones USB should appear
python -c "import sounddevice as sd; print(sd.query_devices())" | grep -i blue
```

### Check Display Server (Critical - Must be X11)
```bash
echo "DISPLAY: $DISPLAY"  # Should show :0 or :1
echo "Session: $XDG_SESSION_TYPE"  # Must show 'x11', NOT 'wayland'
```

---

## 2. Quick Functionality Test (1 minute)

### Test Hotkey Registration
```bash
xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/<Primary>apostrophe" | grep -i dictation
```

### Test Recording Toggle
```bash
cd modules/dictation
./dictation-toggle.sh  # Press Ctrl+' to start
# Speak for 3-5 seconds
./dictation-toggle.sh  # Press Ctrl+' to stop
```

**Expected Results:**
- ✓ Start notification appears
- ✓ Stop notification appears with transcribed text
- ✓ Text appears at cursor position
- ✓ Lock file created and removed

---

## 3. Automated Test Suite (5 minutes)

### Run Unit Tests
```bash
cd modules/dictation
python test_dictate.py
```

### Run Integration Tests
```bash
./test-dictation.sh
```

### Run Manual Test Scripts
```bash
./test-background.sh  # Tests background recording
```

---

## 4. Critical System Checks

### If virtual environment missing:
```bash
cd $HOME/Files/W/Workspace/git/automation-scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dictation.txt
```

### If on Wayland instead of X11:
```bash
# Log out and select "XFCE (X11 session)" from display manager
# The dictation module does NOT support Wayland
```

### If audio device not detected:
```bash
# Check USB connection
lsusb | grep -i audio

# Check PulseAudio
pulseaudio --check && echo "PulseAudio running" || pulseaudio --start

# Restart PulseAudio
pulseaudio -k && pulseaudio --start
```

---

## 5. Common Post-Restart Issues

### Issue: Virtual environment not activated
**Solution:** `source .venv/bin/activate` in every new terminal

### Issue: Wayland session (xdotool won't work)
**Solution:** Log out and select X11 session

### Issue: Microphone not detected
**Solution:** Check USB connection, restart PulseAudio

### Issue: Hotkey not working
**Solution:** Re-run setup: `cd modules/dictation && ./setup.sh`

### Issue: Whisper model won't load
**Solution:** Check internet connection, model downloads on first run (~145MB)

---

## 6. Success Criteria

✓ All unit tests pass
✓ Audio device detected
✓ Recording starts/stops successfully
✓ Hotkey triggers recording
✓ Text appears in application
✓ Notifications display correctly
✓ No Wayland/X11 conflicts

---

## 7. Quick Reset (if something breaks)

```bash
cd $HOME/Files/W/Workspace/git/automation-scripts
rm -rf .venv
./scripts/setup-dev.sh dictation
cd modules/dictation
./setup.sh
./test-dictation.sh
```
