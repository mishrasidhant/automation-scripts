# Dictation Module - Speech-to-Text for Linux

Fast, accurate voice dictation using Whisper AI with seamless hotkey integration.

## ✨ Features

- 🎤 **Instant Dictation**: Press `Ctrl+'` to record, press again to transcribe and paste
- 🚀 **Fast Setup**: Install and run in under 5 minutes
- 🔒 **Reliable**: Hotkey persists across reboots via systemd service
- 🎯 **Accurate**: Powered by OpenAI's Whisper model (base.en by default)
- ⚙️ **Configurable**: TOML configuration with environment variable overrides
- 🛠️ **Diagnostic Tools**: Built-in troubleshooting with `check-hotkey-status.sh`
- 🔐 **Private**: All processing happens locally - no cloud, no data sent anywhere

## 📋 Requirements

- **OS**: Linux (Manjaro/Arch tested, should work on Ubuntu/Debian/Fedora)
- **Desktop**: XFCE with X11 (Wayland not supported yet)
- **Python**: 3.11-3.13 (3.14+ not yet supported - waiting for ctranslate2 wheel builds)
- **System Packages**: portaudio, xdotool, libnotify

## 🚀 Quick Start (5 Minutes)

### 1. Install System Dependencies

**Manjaro/Arch:**
```bash
sudo pacman -S portaudio xdotool libnotify
```

**Ubuntu/Debian:**
```bash
sudo apt install portaudio19-dev xdotool libnotify-bin
```

**Fedora:**
```bash
sudo dnf install portaudio-devel xdotool libnotify
```

### 2. Install UV (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### 3. Clone and Setup

```bash
git clone https://github.com/yourusername/automation-scripts.git
cd automation-scripts
uv sync --extra dictation
```

### 4. Install Systemd Service (Hotkey Persistence)

```bash
./scripts/install-hotkey-service.sh
```

### 5. Test It!

Press `Ctrl+'` to start recording, speak clearly, press `Ctrl+'` again to stop.

Your transcribed text will be typed at the cursor position! 🎉

## 📖 Usage

### Keyboard Shortcut (Recommended)

- **Start recording:** Press `Ctrl+'`
- **Stop & transcribe:** Press `Ctrl+'` again
- **Text appears:** Automatically typed at cursor

### Manual Commands

```bash
# Start recording
uv run dictation-toggle --start

# Stop and transcribe
uv run dictation-toggle --stop

# Toggle (start if stopped, stop if started)
uv run dictation-toggle --toggle
```

## ⚙️ Configuration

### Location

Configuration file: `~/.config/automation-scripts/dictation.toml`

### Basic Example

```toml
[whisper]
model = "base.en"      # Options: tiny.en, base.en, small.en, medium.en, large
device = "cpu"         # Options: cpu, cuda

[text]
typing_delay = 12      # Milliseconds between keystrokes (5-50)
auto_capitalize = false

[notifications]
enable = true
timeout = 3000         # Milliseconds
```

### Complete Configuration

See `config/dictation.toml.example` for all available options.

### Configuration Examples

The repository includes pre-configured examples for different use cases:

- **`config/dictation-minimal.toml`**: Bare minimum setup (model only)
- **`config/dictation-performance.toml`**: Optimized for speed (tiny.en, int8)
- **`config/dictation-accuracy.toml`**: Optimized for accuracy (small.en, beam_size=10)

Copy any of these to `~/.config/automation-scripts/dictation.toml` and customize as needed.

### Environment Variable Overrides

```bash
# Override Whisper model
export DICTATION_WHISPER_MODEL=small.en

# Override typing speed
export DICTATION_TYPING_DELAY=20

# Disable notifications
export DICTATION_NOTIFICATIONS_ENABLED=false
```

Pattern: `DICTATION_<SECTION>_<KEY>` (e.g., `DICTATION_WHISPER_MODEL`)

## 🔍 Troubleshooting

### Check System Health

```bash
./scripts/check-hotkey-status.sh
```

This shows:
- ✅ Systemd service status
- ✅ Hotkey registration
- ✅ UV environment health
- ✅ Recent operation logs

### Common Issues

**Hotkey not working after reboot:**
```bash
systemctl --user status dictation-hotkey.service
# If not enabled:
systemctl --user enable dictation-hotkey.service
systemctl --user start dictation-hotkey.service
```

**Module import failed:**
```bash
cd /path/to/automation-scripts
uv sync --extra dictation
```

**Audio device not found:**
```bash
# List available devices:
python -c "import sounddevice; print(sounddevice.query_devices())"

# Update config:
# ~/.config/automation-scripts/dictation.toml
[audio]
device = "device_name_here"
```

**View detailed logs:**
```bash
cat /tmp/dictation-toggle.log
journalctl --user -u dictation-hotkey.service
```

### Still Having Issues?

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed problem-solving guides.

## 📚 Documentation

- **[User Guide](docs/USER-GUIDE.md)**: Tips for better transcription accuracy
- **[Architecture](docs/ARCHITECTURE.md)**: System design and components
- **[Development](docs/DEVELOPMENT.md)**: Contributing and development setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Detailed problem-solving guide
- **[Migration Guide](docs/MIGRATION-TO-UV.md)**: Upgrading from older versions
- **[Changelog](CHANGELOG.md)**: Version history and changes

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov

# Verbose output
uv run pytest -v
```

See [tests/README.md](tests/README.md) for the complete testing guide.

## 🎯 Performance

- **Model download**: First run only (~140MB for base.en)
- **Transcription speed**: ~2-5 seconds for 10s audio (base.en on CPU)
- **Memory usage**: ~2GB RAM (base.en model)

### Model Comparison

| Model | Size | Speed | Accuracy | RAM |
|-------|------|-------|----------|-----|
| tiny.en | 75MB | ⚡⚡⚡ | ⭐⭐ | ~1GB |
| base.en | 140MB | ⚡⚡ | ⭐⭐⭐ | ~2GB |
| small.en | 460MB | ⚡ | ⭐⭐⭐⭐ | ~3GB |
| medium.en | 1.5GB | 🐢 | ⭐⭐⭐⭐⭐ | ~5GB |

## 🛡️ Privacy

- **All processing is local** - no cloud services, no data sent anywhere
- **Whisper runs offline** - internet only needed for initial model download
- **Temporary files** - audio recordings deleted after transcription (configurable)

## 📝 Architecture

### System Overview

The dictation module uses a multi-layered architecture:

```
User presses Ctrl+'
    ↓
systemd service (dictation-hotkey.service)
    ↓
dictation-toggle.sh (state management, lock file)
    ↓
UV Python environment (auto-synced)
    ↓
Python module (config → audio → transcription → text injection)
    ↓
Text appears at cursor
```

### Key Components

- **`src/automation_scripts/dictation/`**: Python package with UV dependency management
- **`scripts/dictation-toggle.sh`**: Shell wrapper for recording state management
- **`systemd/dictation-hotkey.service`**: Ensures hotkey persists across reboots
- **`config/dictation.toml.example`**: Complete configuration template

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🏗️ Repository Structure

```
automation-scripts/
├── src/
│   └── automation_scripts/
│       └── dictation/          # Python package
│           ├── __init__.py
│           ├── config.py       # Configuration loading
│           ├── constants.py    # XDG paths and defaults
│           └── dictate.py      # Core dictation logic
├── scripts/
│   ├── dictation-toggle.sh     # Recording wrapper
│   ├── install-hotkey-service.sh
│   ├── check-hotkey-status.sh  # Diagnostic tool
│   └── register-hotkey.sh      # Hotkey registration
├── systemd/
│   └── dictation-hotkey.service # Systemd service
├── config/
│   ├── dictation.toml.example  # Full config example
│   ├── dictation-minimal.toml  # Minimal config
│   ├── dictation-performance.toml
│   └── dictation-accuracy.toml
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_config.py         # Config tests
│   ├── test_constants.py      # Constants tests
│   └── README.md              # Testing guide
├── docs/
│   ├── ARCHITECTURE.md        # System design
│   ├── USER-GUIDE.md          # User documentation
│   ├── TROUBLESHOOTING.md     # Problem solving
│   ├── DEVELOPMENT.md         # Developer guide
│   └── MIGRATION-TO-UV.md     # Migration guide
├── pyproject.toml             # UV project config
├── uv.lock                    # Dependency lock file
├── CHANGELOG.md               # Version history
└── README.md                  # This file
```

## 🤝 Contributing

Contributions are welcome! See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:

- Development environment setup
- Running tests
- Code structure
- Adding new features
- Release process

## 📦 Dependencies

Managed by [UV](https://github.com/astral-sh/uv) - fast, reliable Python package management.

**Runtime dependencies:**
- `faster-whisper>=0.10.0` - Optimized Whisper inference
- `sounddevice>=0.4.6` - Audio recording
- `numpy>=1.24.0` - Audio processing

**Development dependencies:**
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `ruff>=0.1.0` - Fast linter

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the amazing speech recognition model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for optimized inference
- [UV](https://github.com/astral-sh/uv) for lightning-fast Python package management

## 📜 License

MIT License - see LICENSE file for details

## 🔖 Version

**v0.1.0** - UV Migration & Enhanced Diagnostics

Key improvements in this release:
- UV-based package management (fast, reliable)
- TOML configuration with XDG compliance
- Systemd service for hotkey persistence
- Comprehensive test suite (58 tests, >70% coverage)
- Enhanced diagnostic tools
- Professional documentation
- Configuration examples for different use cases

For complete version history, see [CHANGELOG.md](CHANGELOG.md).

---

**Author:** Sidhant Dixit  
**Repository:** https://github.com/mishrasidhant/automation-scripts  
**Issues:** https://github.com/mishrasidhant/automation-scripts/issues
