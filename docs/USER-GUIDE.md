# Dictation Module User Guide

Welcome! This guide will help you get the most out of the dictation module - from basic usage to advanced tips for accuracy and customization.

## Table of Contents

- [Getting Started](#getting-started)
- [Basic Usage](#basic-usage)
- [Tips for Better Accuracy](#tips-for-better-accuracy)
- [Customizing Behavior](#customizing-behavior)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Model Selection Guide](#model-selection-guide)
- [Audio Device Selection](#audio-device-selection)
- [Performance Tuning](#performance-tuning)
- [Best Practices](#best-practices)

## Getting Started

### Your First Recording

1. **Press the hotkey**: `Ctrl+'` (or your configured key)
2. **See notification**: "Recording started..."
3. **Speak clearly**: Say what you want to transcribe
4. **Press hotkey again**: `Ctrl+'`
5. **Wait briefly**: Transcription takes 2-5 seconds
6. **See text appear**: Automatically typed at your cursor!

### What Just Happened?

Behind the scenes:
1. Audio recorded from your microphone (16kHz, mono)
2. Saved as temporary WAV file
3. Processed by Whisper AI model (locally, offline)
4. Text cleaned and formatted
5. Injected at cursor via keyboard simulation
6. Temporary audio file deleted

**No data leaves your computer!** Everything runs locally.

## Basic Usage

### Recording Methods

#### Method 1: Keyboard Shortcut (Recommended)

```
Press Ctrl+' → Speak → Press Ctrl+' again
```

**Pros**: Fast, seamless, works in any application
**Cons**: Requires hotkey setup

#### Method 2: Manual Commands

```bash
# Start recording
uv run dictation-toggle --start

# Speak your text...

# Stop and transcribe
uv run dictation-toggle --stop
```

**Pros**: Scriptable, no hotkey needed
**Cons**: Slower, requires terminal access

#### Method 3: Toggle Mode

```bash
# Automatically detects if recording or stopped
uv run dictation-toggle --toggle
```

This is what the hotkey actually runs!

### Where Text Appears

Text is inserted at the **current cursor position** in the **active application**.

**Works with**:
- Text editors (VSCode, Sublime, Vim, Emacs)
- Web browsers (Gmail, Google Docs, any text field)
- Terminal applications
- Office suites (LibreOffice)
- Chat applications (Slack, Discord)

**May not work with**:
- Some proprietary apps with custom text input
- Applications running as root
- Wayland-native applications (X11 compatibility mode may work)

## Tips for Better Accuracy

### Speaking Technique

**Do:**
- Speak clearly and at moderate pace
- Use natural sentence structure
- Pause briefly for punctuation
- Speak in a quiet environment
- Position microphone 6-12 inches from mouth

**Don't:**
- Mumble or speak too quickly
- Include background noise (TV, music)
- Use poor quality microphone
- Speak too softly or too loudly
- Cut words short or slur

### Punctuation

Whisper can recognize some punctuation if you say it naturally:

**Works well**:
- Periods: Natural pause at sentence end
- Question marks: Rising intonation
- Commas: Brief pause mid-sentence

**Less reliable**:
- Exclamation marks
- Quotation marks
- Semicolons, colons

**Workaround**: Add punctuation manually after transcription, or use text processing rules in config.

### Capitalization

By default, Whisper determines capitalization. You can override with configuration:

```toml
[text]
auto_capitalize = true  # Capitalize first letter of transcription
```

### Numbers and Dates

Whisper handles numbers well:
- "one hundred twenty three" → "123" (usually)
- "twenty twenty four" → "2024"
- "January first" → "January 1st"

**Note**: Results vary. Some models preserve written-out numbers.

### Technical Terms and Jargon

Whisper is trained on diverse internet text, so it knows:
- Programming terms: "Python", "JavaScript", "API"
- Technical jargon: "Kubernetes", "Docker", "REST"
- Brand names: "GitHub", "Amazon", "Microsoft"

**For specialized vocabulary**, consider:
- Using larger models (small.en, medium.en)
- Speaking more slowly and clearly
- Correcting common mistakes in post-processing

## Customizing Behavior

### Configuration File

**Location**: `~/.config/automation-scripts/dictation.toml`

**To customize**:

1. Copy the example:
```bash
mkdir -p ~/.config/automation-scripts
cp config/dictation.toml.example ~/.config/automation-scripts/dictation.toml
```

2. Edit with your preferred editor:
```bash
vim ~/.config/automation-scripts/dictation.toml
```

3. Test your changes:
```bash
uv run dictation-toggle --start
```

Changes take effect immediately (no restart needed).

### Quick Overrides with Environment Variables

For temporary changes, use environment variables:

```bash
# Try a different model
DICTATION_WHISPER_MODEL=small.en uv run dictation-toggle --start

# Adjust typing speed
DICTATION_TYPING_DELAY=20 uv run dictation-toggle --start

# Disable notifications
DICTATION_NOTIFICATIONS_ENABLED=false uv run dictation-toggle --start
```

Environment variables override TOML config.

### Common Customizations

#### Faster Transcription (Lower Accuracy)

```toml
[whisper]
model = "tiny.en"
compute_type = "int8"
beam_size = 1
```

#### Better Accuracy (Slower)

```toml
[whisper]
model = "small.en"
compute_type = "float16"
beam_size = 10
```

#### Clipboard Instead of Typing

```toml
[text]
paste_method = "clipboard"
```

Now you manually paste with `Ctrl+V` after transcription.

#### Silent Mode (No Notifications)

```toml
[notifications]
enable = false
```

#### Keep Audio Files for Review

```toml
[files]
keep_temp_files = true
temp_dir = "/tmp/dictation"
```

Find recordings in `/tmp/dictation/recording_*.wav`

## Keyboard Shortcuts

### Default Hotkey

**`Ctrl+'`** (Control + Apostrophe)

Toggle recording on/off.

### Changing the Hotkey

#### Method 1: Using the Script

```bash
# Unregister current hotkey
./scripts/unregister-hotkey.sh

# Edit register-hotkey.sh to change key combination
# Then re-register
./scripts/register-hotkey.sh
```

#### Method 2: XFCE Settings (Manual)

1. Open Settings → Keyboard → Application Shortcuts
2. Find the dictation-toggle.sh entry
3. Click it and press new key combination
4. Reload: `systemctl --user reload dictation-hotkey.service`

### Key Combination Ideas

- `Ctrl+Shift+D` - "D" for dictation
- `Super+Space` - Quick access
- `Ctrl+Alt+V` - "V" for voice
- `F12` - Function key

Choose something that doesn't conflict with other shortcuts!

## Model Selection Guide

### Available Models

| Model | Size | Speed | Accuracy | RAM | Best For |
|-------|------|-------|----------|-----|----------|
| tiny.en | 75MB | ⚡⚡⚡ Very Fast | ⭐⭐ Fair | 1GB | Quick notes, fast hardware |
| base.en | 140MB | ⚡⚡ Fast | ⭐⭐⭐ Good | 2GB | **Default, balanced use** |
| small.en | 460MB | ⚡ Moderate | ⭐⭐⭐⭐ Great | 3GB | Accuracy matters, longer text |
| medium.en | 1.5GB | 🐢 Slow | ⭐⭐⭐⭐⭐ Excellent | 5GB | Best quality, GPU recommended |
| large-v3 | 2.9GB | 🐌 Very Slow | ⭐⭐⭐⭐⭐ Best | 10GB | Production transcription, GPU required |

### Choosing a Model

**Use tiny.en if**:
- You want fast results
- You have limited RAM
- You're transcribing simple, clear speech
- Speed > accuracy

**Use base.en if**: (Default, recommended for most users)
- You want balanced performance
- You have 4GB+ RAM
- You transcribe various content
- Good enough accuracy

**Use small.en if**:
- Accuracy is important
- You have 8GB+ RAM
- You transcribe technical content
- You can wait a bit longer

**Use medium.en or large-v3 if**:
- You need the best possible accuracy
- You have a GPU (CUDA)
- You transcribe professionally
- You have 16GB+ RAM

### Switching Models

**Edit config file**:
```toml
[whisper]
model = "small.en"
```

**Or use environment variable**:
```bash
DICTATION_WHISPER_MODEL=small.en uv run dictation-toggle --start
```

**First run downloads the model** (~30 seconds to 5 minutes depending on model size).

### English-Only vs Multilingual

**English-only models** (tiny.en, base.en, small.en, medium.en):
- Faster
- More accurate for English
- Smaller file size
- **Recommended for English users**

**Multilingual models** (tiny, base, small, medium, large):
- Support 90+ languages
- Slightly slower
- Larger file size
- Use with `language = "en"` config for English

## Audio Device Selection

### Finding Your Microphone

List all audio devices:

```bash
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**Example output**:
```
0 Built-in Audio Analog Stereo, ALSA (2 in, 2 out)
1 USB Audio Device, ALSA (1 in, 0 out)
2 Bluetooth Headset, PulseAudio (1 in, 1 out)
```

### Selecting a Device

**Use device name**:
```toml
[audio]
device = "USB Audio Device"
```

**Use device index**:
```toml
[audio]
device = "1"
```

**Use system default**:
```toml
[audio]
device = "default"
```

### Microphone Quality Matters

**Built-in laptop mic**: Usually acceptable
**USB microphone**: Better quality
**Bluetooth headset**: May have latency issues
**Professional mic**: Best quality

**Recommendation**: USB microphone for regular use (e.g., Blue Yeti, Rode NT-USB).

## Performance Tuning

### Speed vs Accuracy Trade-Offs

#### Maximum Speed Configuration

```toml
[whisper]
model = "tiny.en"
device = "cpu"
compute_type = "int8"
beam_size = 1
temperature = 0.0
vad_filter = true

[text]
typing_delay = 5
```

**Expected**: ~1-2 seconds for 10s audio

#### Maximum Accuracy Configuration

```toml
[whisper]
model = "small.en"
device = "cpu"
compute_type = "float16"
beam_size = 10
temperature = 0.0
vad_filter = true

[text]
typing_delay = 15
```

**Expected**: ~5-8 seconds for 10s audio

### GPU Acceleration

If you have an NVIDIA GPU with CUDA:

```toml
[whisper]
device = "cuda"
compute_type = "float16"
model = "medium.en"
```

**Speed improvement**: 5-10x faster transcription!

**Note**: Requires CUDA toolkit and compatible GPU.

### Typing Speed Adjustment

If text gets corrupted (missed characters), increase typing delay:

```toml
[text]
typing_delay = 20  # Slower but more reliable
```

If typing is too slow:

```toml
[text]
typing_delay = 8  # Faster but may miss characters
```

**Sweet spot**: 10-15ms for most systems.

## Best Practices

### Recording Length

**Optimal**: 5-30 seconds
- Short enough for quick transcription
- Long enough to capture complete thoughts
- Whisper works best with sentence-length audio

**Too short** (< 2 seconds):
- May not capture full context
- Accuracy can suffer

**Too long** (> 60 seconds):
- Takes longer to transcribe
- More likely to include unwanted sounds
- Harder to manage errors

### Environment Setup

**For best results**:
1. **Quiet room**: Close windows, turn off fans
2. **Good microphone**: USB mic > built-in
3. **Proper positioning**: 6-12 inches from mouth
4. **Stable surface**: Don't move mic during recording
5. **Consistent volume**: Not too loud (clipping) or soft

### Workflow Integration

**Writing emails**:
```
1. Draft outline manually
2. Press Ctrl+' for each paragraph
3. Review and edit transcribed text
4. Send
```

**Coding documentation**:
```
1. Write code first
2. Use dictation for comments/docstrings
3. Format with linter
```

**Note-taking**:
```
1. Listen to lecture/meeting
2. Press Ctrl+' for key points
3. Organize notes later
```

### Handling Errors

**If transcription is wrong**:
- Try recording again (often faster than editing)
- Use smaller sentences
- Speak more clearly
- Check microphone quality

**If text doesn't appear**:
- Check xdotool is installed: `which xdotool`
- Increase typing_delay in config
- Try paste_method = "clipboard" as fallback

**If recording won't start**:
- Check system status: `./scripts/check-hotkey-status.sh`
- Look at logs: `tail -20 /tmp/dictation-toggle.log`
- Restart service: `systemctl --user restart dictation-hotkey.service`

### Privacy Considerations

**Your audio never leaves your computer!**

The dictation module:
- ✅ Runs entirely offline (after model download)
- ✅ Deletes temporary audio files (by default)
- ✅ Doesn't send data to any servers
- ✅ Doesn't require internet connection (after setup)

**If you want extra privacy**:
```toml
[files]
keep_temp_files = false  # Delete audio immediately
temp_dir = "/tmp/dictation"  # Use tmpfs (RAM-based, never written to disk)
```

## Advanced Tips

### Custom Text Processing

Edit `src/automation_scripts/dictation/dictate.py` function `process_text()` to add custom rules:

```python
def process_text(text: str) -> str:
    # Custom replacements
    text = text.replace("python", "Python")
    text = text.replace("github", "GitHub")
    
    # Add your rules here
    return text
```

### Batch Processing

Record multiple voice notes without stopping:

```bash
# Record note 1
uv run dictation-toggle --start
# Speak...
uv run dictation-toggle --stop

# Record note 2
uv run dictation-toggle --start
# Speak...
uv run dictation-toggle --stop
```

Each recording transcribes separately.

### Using with Other Applications

**With clipboard manager** (e.g., CopyQ):
```toml
[text]
paste_method = "both"  # Types AND copies to clipboard
```

Now you have a history of all transcriptions!

**With text expander** (e.g., espanso):
Transcribe, then use text expander shortcuts to format.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed problem-solving.

**Quick fixes**:

**No audio recorded**: Check microphone in system settings
**Poor accuracy**: Try larger model (small.en or medium.en)
**Slow transcription**: Try smaller model (tiny.en) or enable GPU
**Hotkey not working**: Run `./scripts/check-hotkey-status.sh`
**Import errors**: Run `uv sync --extra dictation`

## Getting Help

If you're stuck:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Run diagnostic: `./scripts/check-hotkey-status.sh`
3. Check logs: `tail -50 /tmp/dictation-toggle.log`
4. File an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Output of diagnostic script
   - System information (OS, desktop environment)

## Summary

**Quick Reference**:
- **Start/stop**: `Ctrl+'`
- **Config**: `~/.config/automation-scripts/dictation.toml`
- **Logs**: `/tmp/dictation-toggle.log`
- **Diagnostic**: `./scripts/check-hotkey-status.sh`
- **Default model**: base.en (140MB, 2GB RAM)

**For best results**:
- Speak clearly in a quiet environment
- Use a good microphone
- Record 5-30 second clips
- Review and edit transcriptions

**Remember**: The more you use it, the better you'll get at dictating effectively. Happy transcribing! 🎤

