# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the dictation module.

## Table of Contents

- [Quick Diagnostic](#quick-diagnostic)
- [Hotkey Issues](#hotkey-issues)
- [Audio Recording Issues](#audio-recording-issues)
- [Transcription Issues](#transcription-issues)
- [Text Injection Issues](#text-injection-issues)
- [Performance Issues](#performance-issues)
- [Installation Issues](#installation-issues)
- [Log Files and Debugging](#log-files-and-debugging)
- [Known Limitations](#known-limitations)
- [Getting Help](#getting-help)

## Quick Diagnostic

**First step for any issue**: Run the diagnostic script:

```bash
./scripts/check-hotkey-status.sh
```

This checks:
- ✅ Systemd service status
- ✅ Hotkey registration
- ✅ UV environment health
- ✅ Python module imports
- ✅ Recent logs

**Example output**:
```
=== Dictation Hotkey Diagnostic ===

[✓] Systemd Service
    Status: active (running)
    Enabled: yes
    
[✓] Hotkey Registration
    Keyboard shortcut: Ctrl+apostrophe
    Command: /home/user/automation-scripts/scripts/dictation-toggle.sh
    
[✓] UV Environment
    Python: 3.13.7
    Module: importable
    Dependencies: synced
    
[✓] Recent Logs
    Last 5 operations:
    [2025-10-28 14:32:10] Recording started
    [2025-10-28 14:32:18] Transcription complete: hello world
    
No issues detected!
```

## Hotkey Issues

### Issue: Hotkey Doesn't Work After Reboot

**Symptoms**:
- `Ctrl+'` does nothing
- Worked before, stopped after restart
- No notification appears

**Diagnosis**:
```bash
systemctl --user status dictation-hotkey.service
```

**Solution 1**: Service not running
```bash
systemctl --user start dictation-hotkey.service
```

**Solution 2**: Service not enabled (won't start on boot)
```bash
systemctl --user enable dictation-hotkey.service
systemctl --user start dictation-hotkey.service
```

**Solution 3**: Service failed to start
```bash
# Check service logs
journalctl --user -u dictation-hotkey.service --no-pager -n 20

# Common issues:
# - Script path incorrect → Update service file
# - XFCE not running → Wait for desktop to start
# - Permissions error → chmod +x scripts/*.sh
```

**Solution 4**: XFCE settings not persisting
```bash
# Reload XFCE settings daemon
killall -HUP xfce4-settings-helper

# Or reload service
systemctl --user reload dictation-hotkey.service
```

### Issue: Hotkey Triggers Wrong Command

**Symptoms**:
- `Ctrl+'` runs something else
- Multiple actions happen at once

**Diagnosis**:
```bash
xfconf-query -c xfce4-keyboard-shortcuts -l -v | grep -i "ctrl.*apostrophe"
```

**Solution**: Conflicting shortcut registered
```bash
# Unregister all hotkeys for this command
./scripts/unregister-hotkey.sh

# Re-register clean
./scripts/register-hotkey.sh

# Restart XFCE settings helper
killall -HUP xfce4-settings-helper
```

### Issue: Hotkey Works But Nothing Happens

**Symptoms**:
- `Ctrl+'` triggers something (you can tell)
- No notification appears
- No recording starts

**Diagnosis**:
```bash
# Check if script is executable
ls -la scripts/dictation-toggle.sh

# Try running manually
./scripts/dictation-toggle.sh --toggle
```

**Solutions**:

**Script not executable**:
```bash
chmod +x scripts/dictation-toggle.sh
chmod +x scripts/register-hotkey.sh
chmod +x scripts/unregister-hotkey.sh
```

**Python module not importable**:
```bash
cd /path/to/automation-scripts
uv sync --extra dictation
```

**UV not in PATH**:
```bash
# Add to ~/.bashrc or ~/.profile
export PATH="$HOME/.local/bin:$PATH"

# Or install UV again
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Audio Recording Issues

### Issue: No Audio Recorded

**Symptoms**:
- Recording starts (notification)
- Recording stops (notification)
- Transcription empty or "no speech detected"

**Diagnosis**:
```bash
# Test audio recording manually
arecord -d 3 -f cd test.wav
aplay test.wav
# Can you hear yourself?
```

**Solution 1**: Wrong audio device selected
```bash
# List all audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Update config with correct device
vim ~/.config/automation-scripts/dictation.toml
```

```toml
[audio]
device = "USB Audio Device"  # Use actual device name
```

**Solution 2**: Microphone muted or volume too low
```bash
# Check microphone settings in XFCE
xfce4-mixer
# or
pavucontrol  # If using PulseAudio
```

**Solution 3**: PortAudio not installed
```bash
sudo pacman -S portaudio  # Arch/Manjaro
sudo apt install portaudio19-dev  # Ubuntu/Debian
```

**Solution 4**: Permissions issue
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

### Issue: Audio Choppy or Distorted

**Symptoms**:
- Recording completes
- Playback sounds garbled
- Transcription inaccurate

**Solution 1**: Buffer size too small
```toml
[performance]
buffer_size = 2048  # Increase from default 1024
```

**Solution 2**: CPU overloaded
```bash
# Check CPU usage during recording
top
# If high: Close other applications
```

**Solution 3**: USB microphone issue
```bash
# Try different USB port
# Use USB 2.0 port instead of 3.0 (sometimes more stable)
```

### Issue: Recording Won't Stop

**Symptoms**:
- Press `Ctrl+'` again
- Notification doesn't appear
- Recording continues indefinitely

**Diagnosis**:
```bash
# Check if recording process is running
ps aux | grep dictation
# Check lock file
cat /tmp/dictation.lock
```

**Solution**:
```bash
# Kill recording process (use PID from lock file)
kill -TERM <PID>

# Or force kill if unresponsive
kill -9 <PID>

# Clean up lock file
rm /tmp/dictation.lock

# Try again
./scripts/dictation-toggle.sh --toggle
```

## Transcription Issues

### Issue: Poor Transcription Accuracy

**Symptoms**:
- Words consistently wrong
- Missing words
- Nonsense output

**Solutions**:

**Use larger model**:
```toml
[whisper]
model = "small.en"  # Better than base.en
# or
model = "medium.en"  # Best quality
```

**Improve recording quality**:
- Use external USB microphone
- Record in quiet environment
- Speak clearly and at moderate pace
- Position mic 6-12 inches from mouth

**Adjust beam search**:
```toml
[whisper]
beam_size = 10  # More thorough (default: 5)
```

**Check language setting**:
```toml
[whisper]
language = "en"  # Ensure English for .en models
```

### Issue: Transcription Very Slow

**Symptoms**:
- Takes 30+ seconds for 10s audio
- CPU usage very high
- System sluggish during transcription

**Solutions**:

**Use smaller/faster model**:
```toml
[whisper]
model = "tiny.en"  # Much faster
compute_type = "int8"  # Fastest compute
```

**Enable GPU acceleration** (if available):
```toml
[whisper]
device = "cuda"  # Requires NVIDIA GPU + CUDA
compute_type = "float16"
```

**Reduce beam size**:
```toml
[whisper]
beam_size = 1  # Fastest (less accurate)
```

**Close other applications**:
```bash
# Check what's using CPU
top
# Close unnecessary programs
```

### Issue: "Model Not Found" Error

**Symptoms**:
- Error message about missing model
- Transcription fails immediately

**Solution**:
```bash
# Model cache should be in:
# ~/.cache/automation-scripts/dictation/models/

# If missing, model will download on next run
# Ensure you have internet connection

# Force model download
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu')"
```

### Issue: Import Error for faster-whisper

**Symptoms**:
```
ModuleNotFoundError: No module named 'faster_whisper'
```

**Solution**:
```bash
cd /path/to/automation-scripts
uv sync --extra dictation

# Verify installation
uv run python -c "import faster_whisper; print('OK')"
```

## Text Injection Issues

### Issue: Text Doesn't Appear

**Symptoms**:
- Recording and transcription complete
- Notification shows transcribed text
- Text doesn't appear in application

**Diagnosis**:
```bash
# Check if xdotool is installed
which xdotool

# Test xdotool manually
xdotool type "test"
```

**Solution 1**: xdotool not installed
```bash
sudo pacman -S xdotool  # Arch/Manjaro
sudo apt install xdotool  # Ubuntu/Debian
```

**Solution 2**: Wrong paste method
```toml
[text]
paste_method = "xdotool"  # Not "clipboard"
```

**Solution 3**: Application doesn't accept simulated input
```bash
# Some apps block xdotool
# Try clipboard method instead
```

```toml
[text]
paste_method = "clipboard"
```

Then manually paste with `Ctrl+V`.

**Solution 4**: Wayland (not X11)
```bash
# Check if Wayland
echo $XDG_SESSION_TYPE
# If "wayland": xdotool won't work

# Workarounds:
# 1. Use X11 compatibility mode
# 2. Use clipboard paste method
# 3. Try wtype (Wayland alternative to xdotool)
```

### Issue: Missing or Corrupted Characters

**Symptoms**:
- Most text appears correctly
- Some characters missing
- Text garbled or wrong

**Solution**: Increase typing delay
```toml
[text]
typing_delay = 20  # Increase from default 12
```

**If still issues**:
```toml
[text]
typing_delay = 30  # Even slower
paste_method = "both"  # Also copy to clipboard as backup
```

### Issue: Text Appears in Wrong Application

**Symptoms**:
- Text appears somewhere else
- Active window changed during transcription

**Solution**:
- Ensure target application stays focused during transcription
- Don't switch windows during the 2-5 second processing time
- Use clipboard method if you need to switch windows:

```toml
[text]
paste_method = "clipboard"
```

## Performance Issues

### Issue: High Memory Usage

**Symptoms**:
- System slow during transcription
- RAM usage spikes
- Swap space being used

**Solution 1**: Use smaller model
```toml
[whisper]
model = "tiny.en"  # Uses ~1GB instead of ~2GB
```

**Solution 2**: Close other applications
```bash
# Check memory usage
free -h
# Close memory-hungry apps
```

**Solution 3**: Increase swap
```bash
# Check current swap
swapon --show
# If no swap or low, consider adding more
```

### Issue: Disk Space Running Out

**Symptoms**:
- Error: "No space left on device"
- /tmp full

**Solution 1**: Clean temporary files
```bash
# Remove old audio files
rm /tmp/dictation/*.wav

# Check disk space
df -h /tmp
```

**Solution 2**: Change temp directory
```toml
[files]
temp_dir = "/home/user/tmp/dictation"  # Use home partition
```

**Solution 3**: Disable keep_temp_files
```toml
[files]
keep_temp_files = false  # Delete after transcription
```

### Issue: Model Download Fails

**Symptoms**:
- "Could not download model" error
- Hangs during first run
- Network timeout

**Solution**:
```bash
# Check internet connection
ping -c 3 huggingface.co

# Try manual download
uv run python -c "
from faster_whisper import WhisperModel
model = WhisperModel('base.en', device='cpu', download_root='~/.cache/automation-scripts/dictation/models')
print('Download complete')
"

# If behind proxy, set proxy environment variables
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

## Installation Issues

### Issue: UV Not Found

**Symptoms**:
```
bash: uv: command not found
```

**Solution**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
uv --version
```

### Issue: Python Version Too Old

**Symptoms**:
```
Error: Python 3.11+ required
```

**Solution**:
```bash
# Check Python version
python3 --version

# UV can install correct Python
uv python install 3.11

# Or install system Python 3.11+
sudo pacman -S python  # Arch/Manjaro
sudo apt install python3.11  # Ubuntu/Debian
```

### Issue: UV Sync Fails

**Symptoms**:
```
error: Failed to sync dependencies
```

**Diagnosis**:
```bash
# Check uv.lock file exists
ls -la uv.lock

# Try verbose output
uv sync --extra dictation -v
```

**Solution 1**: Corrupted lock file
```bash
# Regenerate lock file
rm uv.lock
uv lock
uv sync --extra dictation
```

**Solution 2**: Network issues
```bash
# Retry with different timeout
uv sync --extra dictation --timeout 300
```

**Solution 3**: Dependency conflict
```bash
# Check for conflicts
uv pip list
# Update dependencies
uv sync --extra dictation --upgrade
```

### Issue: Systemd Service Won't Install

**Symptoms**:
- `install-hotkey-service.sh` fails
- Service file not found

**Solution**:
```bash
# Check systemd user directory exists
mkdir -p ~/.config/systemd/user

# Run install script with bash explicitly
bash ./scripts/install-hotkey-service.sh

# Check for errors in output
systemctl --user status dictation-hotkey.service
```

## Log Files and Debugging

### Log Locations

**Dictation toggle log**:
```bash
tail -f /tmp/dictation-toggle.log
```

**Systemd service log**:
```bash
journalctl --user -u dictation-hotkey.service -f
```

**UV environment log**:
```bash
# UV doesn't log by default, but you can enable debug mode
UV_LOG=debug uv sync --extra dictation
```

### Enabling Debug Mode

**Enable verbose logging**:
```bash
# Set environment variable
export DICTATION_DEBUG=1

# Run dictation
uv run dictation-toggle --start
```

**Check recent logs**:
```bash
# Last 50 lines
tail -50 /tmp/dictation-toggle.log

# Last 20 systemd entries
journalctl --user -u dictation-hotkey.service -n 20
```

### Common Log Messages

**"Lock file exists"**:
- Recording already in progress
- Or: Stale lock file (previous recording crashed)
- Solution: `rm /tmp/dictation.lock`

**"Module not found"**:
- UV environment not synced
- Solution: `uv sync --extra dictation`

**"Audio device not found"**:
- Wrong device name in config
- Solution: Check device name with `sounddevice.query_devices()`

**"Transcription failed"**:
- Model not loaded
- Out of memory
- Corrupted audio file
- Solution: Check logs for specific error

## Known Limitations

### Platform Limitations

**Wayland not supported**:
- xdotool requires X11
- Workaround: Use X11 compatibility mode or clipboard method

**XFCE-optimized**:
- Hotkey registration uses xfconf-query
- Other desktops: May need manual hotkey setup

**Linux-only**:
- No Windows or macOS support currently
- Relies on Linux-specific tools (xdotool, systemd)

### Functional Limitations

**Single recording at a time**:
- Lock file prevents simultaneous recordings
- Must stop current recording before starting new one

**No streaming transcription**:
- Must finish recording before transcription starts
- No real-time partial results

**CPU-intensive**:
- Transcription uses 100% CPU during processing
- Can make system sluggish on slower hardware

**Model download required**:
- First run downloads 75MB-3GB (depending on model)
- Requires internet connection initially

### Language Limitations

**English-optimized**:
- .en models only support English
- Multilingual models available but larger and slower

**Accent sensitivity**:
- Trained primarily on American English
- Other accents may have lower accuracy

## Getting Help

### Before Asking for Help

1. **Run diagnostic**: `./scripts/check-hotkey-status.sh`
2. **Check logs**: `tail -50 /tmp/dictation-toggle.log`
3. **Search this document** for your issue
4. **Try with default config**: Rename your config temporarily

### Information to Include

When reporting an issue, please include:

```bash
# System information
uname -a
echo $XDG_SESSION_TYPE

# Python version
python3 --version

# UV version
uv --version

# Package versions
uv pip list | grep -E "faster-whisper|sounddevice|numpy"

# Diagnostic output
./scripts/check-hotkey-status.sh

# Recent logs
tail -30 /tmp/dictation-toggle.log

# Configuration (sanitize sensitive data)
cat ~/.config/automation-scripts/dictation.toml
```

### Where to Get Help

**GitHub Issues**: https://github.com/mishrasidhant/automation-scripts/issues
- Bug reports
- Feature requests
- General questions

**Documentation**:
- [README.md](../README.md) - Quick start and overview
- [USER-GUIDE.md](USER-GUIDE.md) - Usage tips and best practices
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
- [DEVELOPMENT.md](DEVELOPMENT.md) - Contributing guide

### Emergency Recovery

**If everything is broken**:

```bash
# 1. Stop all dictation processes
pkill -f dictation
rm /tmp/dictation.lock

# 2. Reset configuration
mv ~/.config/automation-scripts/dictation.toml ~/.config/automation-scripts/dictation.toml.backup

# 3. Reinstall dependencies
cd /path/to/automation-scripts
rm uv.lock
uv sync --extra dictation

# 4. Reinstall systemd service
./scripts/unregister-hotkey.sh
systemctl --user disable --now dictation-hotkey.service
./scripts/install-hotkey-service.sh

# 5. Test manually
./scripts/dictation-toggle.sh --toggle
```

---

**Still stuck?** File an issue on GitHub with all diagnostic information!

