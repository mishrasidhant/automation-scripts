# ⚙️ automation-scripts

A modular monorepo for managing **system-level automation tools and scripts**.  
Each automation is **self-contained** and **independently deployable** — modules can be standalone scripts, hotkey-triggered utilities, systemd services, client-server architectures, or any combination that fits the use case.

---

## 🧩 Architecture Overview

automation-scripts/
├── README.md # Repository overview and module design guide
│
├── modules/ # Independent automation modules
│ ├── dictation/ # Voice-to-text with hotkey trigger (Python + XFCE)
│ │ ├── dictate.py # Core: audio recording + AI transcription
│ │ ├── dictation-toggle.sh # Wrapper: hotkey integration + state management
│ │ ├── setup.sh # Automated setup + dependency installation
│ │ ├── config/ # Module-specific configuration
│ │ │ └── dictation.env # Settings (model, audio device, paths, etc.)
│ │ └── README.md # User guide and troubleshooting
│ │
│ ├── borg-backup/ # (Future) Automated backup with systemd scheduling
│ │ ├── backup.sh # Full-featured backup + prune + compact routine
│ │ ├── borg-backup.service # systemd unit for manual/triggered runs
│ │ ├── borg-backup.timer # systemd timer for scheduled runs
│ │ ├── config/ # Module-local settings
│ │ │ └── borg-backup.env # Customizable variables (dirs, repo name, etc.)
│ │ └── README.md # Configuration and operational details
│ │
│ └── ... # Future automations (network monitor, sync tool, etc.)
│
├── staging/ # Experimental scripts being tested before module promotion
|
├── scripts/ # Shared utility scripts and cross-module tools
│ ├── setup-dev.sh # Development environment setup
│ └── ... # Future utilities (install helpers, shared functions, etc.)
│
└── docs/ # Developer documentation and standards
    ├── ARCHITECTURE_SUMMARY.md # Quick reference for architecture decisions
    ├── DICTATION_ARCHITECTURE.md # Dictation module technical design
    ├── SYSTEM_PROFILE.md # System-specific configuration and recommendations
    ├── SETUP_CHECKLIST.md # Pre-flight validation and dependency setup
    ├── ENVIRONMENT_SETUP.md # Environment configuration guide
    └── stories/ # Module implementation stories (user stories + specs)


---

## 🧱 Repository Purpose

`automation-scripts` is designed to:

- Serve as a **single home** for diverse automation tools and scripts.
- Keep **modules decoupled** — each module is self-contained and independently deployable.
- Support **multiple deployment patterns** — hotkey-triggered, systemd services, cron jobs, client-server, or standalone.
- Encourage **clarity, reusability, and minimal coupling** — modules can work independently or be composed together.

---

## 🗣️ Example Module: Dictation (Voice-to-Text)

**Status:** ✅ Implemented  
**Pattern:** Hotkey-triggered standalone Python script

This module adds a **local voice dictation utility** that records from the microphone, transcribes speech using faster-whisper AI, and pastes text into the active cursor position.

**System-Optimized:** Architecture has been tailored for **Manjaro Linux + XFCE + X11** based on comprehensive system detection.

**Key components:**
- `dictate.py` — Core recording and transcription logic (faster-whisper).
- `dictation-toggle.sh` — Wrapper script for state management and hotkey integration.
- `config/dictation.env` — User-configurable settings (model, audio device, etc.).
- `setup.sh` — Automated dependency installation and XFCE hotkey registration.
- `test_dictate.py` — Comprehensive test suite for validation.

**Usage:**
Press `Ctrl+'` (configurable) → speak → press again → text appears at your cursor.

**Documentation:**
- 📋 [Quick Summary](docs/ARCHITECTURE_SUMMARY.md) - Key decisions and overview
- 🏗️ [Full Architecture](docs/DICTATION_ARCHITECTURE.md) - Technical deep-dive
- 🖥️ [System Profile](docs/SYSTEM_PROFILE.md) - Hardware/software inventory
- ✅ [Setup Checklist](docs/SETUP_CHECKLIST.md) - Pre-flight validation

---

## 💾 Future Module: Borg Backup Automation

**Status:** 🚧 Planned  
**Pattern:** Systemd service + timer scheduling

A robust Borg-based backup pipeline with integrated logging, pruning, and repository compaction.

**Planned components:**
- `backup.sh` — Orchestrates backup, prune, and compact phases with fault tolerance.
- `borg-backup.service` — Runs backups manually or via trigger.
- `borg-backup.timer` — Daily/weekly timer for scheduled jobs.
- `config/backup.env` — Define `$BACKUP_DIR`, `$BORG_REPO`, exclusions, etc.

**Example use:**
```bash
systemctl --user start borg-backup.service
systemctl --user enable borg-backup.timer
```

This demonstrates the repository's flexibility — systemd-based scheduling works great for some automations, while others (like dictation) use different patterns.

---


## 🧩 Extending the Repo

To add a new automation module:

1. **Create module directory:**
   ```bash
   mkdir -p modules/my-automation/config
   ```

2. **Add module components:**
   - Core script(s) (`my-automation.py`, `my-automation.sh`, etc.)
   - Configuration file in `config/` directory
   - Setup script (optional, for automated installation)
   - `README.md` with usage guide and configuration options
   - Test suite (optional but recommended)

3. **Choose deployment pattern:**
   - **Hotkey-triggered:** Register with desktop environment (like dictation)
   - **Systemd service:** Create `.service` and/or `.timer` files
   - **Cron job:** Add to user or system crontab
   - **Client-server:** Set up daemon + client interface
   - **Standalone:** Run manually or via other triggers

Each module remains **self-contained** and **independent** of others until explicitly coupled.

---

## 🧠 Design Principles

* **Local-first:** Automations run entirely on-device (no cloud dependencies).
* **Modular:** Each module is self-contained with its own configuration and dependencies.
* **Decoupled:** Logic, configuration, and orchestration live in their own layers.
* **Pattern-agnostic:** Use the deployment pattern that fits the automation (hotkeys, systemd, cron, client-server, etc.).
* **Composable:** Modules can be chained, triggered, or scheduled dynamically.
* **Transparent:** Scripts remain simple, auditable, and portable.

---

## 📦 Setup

### Prerequisites

**UV Package Manager** (required):
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or run:
source $HOME/.local/bin/env
```

**System Dependencies** (Arch/Manjaro):
```bash
# Required for dictation module
sudo pacman -S portaudio xdotool libnotify
```

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/mishrasidhant/automation-scripts.git
cd automation-scripts

# 2. Install dependencies with UV (fast: < 30 seconds)
uv sync --extra dictation

# 3. Run dictation
uv run dictation-toggle --start
# Speak into your microphone...
uv run dictation-toggle --stop
# Text appears at your cursor!
```

### Configuration

Configuration is now managed via TOML files following XDG Base Directory specification:

```bash
# Copy example configuration
mkdir -p ~/.config/automation-scripts
cp config/dictation.toml.example ~/.config/automation-scripts/dictation.toml

# Edit configuration
vim ~/.config/automation-scripts/dictation.toml

# Or use environment variables for quick overrides
export DICTATION_WHISPER_MODEL=tiny.en
export DICTATION_TYPING_DELAY=20
uv run dictation-toggle --start
```

### Setting Up the Dictation Module with Hotkey

To bind dictation to a keyboard shortcut (e.g., `Ctrl+'`):

**XFCE (Manjaro default):**
1. Open Settings → Keyboard → Application Shortcuts
2. Add new shortcut
3. Command: `/path/to/automation-scripts/scripts/dictation-toggle.sh`
4. Key: Press `Ctrl+'` (or your preferred key combination)

Now pressing `Ctrl+'` toggles recording!

For complete setup instructions, see [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md).

### Development Setup

```bash
# Setup development environment with UV
source scripts/setup-dev.sh dictation

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/
```

---

**Author:** Sidhant Dixit  
**License:** MIT  
**Version:** 0.1.0 (UV Migration Release)