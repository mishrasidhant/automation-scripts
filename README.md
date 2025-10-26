# ⚙️ systemd-automations

A modular monorepo for managing **system-level automation scripts** and their corresponding `systemd` services.  
Each automation is **self-contained** — it can exist independently or be linked with a `systemd` unit when ready for deployment.

---

## 🧩 Architecture Overview

systemd-automations/
├── README.md # Repository overview and module design guide
│
├── modules/ # Independent automation modules
│ ├── dictation/ # Example 1: Whisper-based dictation app
│ │ ├── dictation.py # Captures mic audio and transcribes via whisper.cpp
│ │ ├── dictation-hotkey.sh # Triggered by keyboard shortcut (e.g. xbindkeys)
│ │ ├── dictation.service # Optional systemd unit for background mode
│ │ ├── config/ # Module-specific configuration
│ │ │ └── dictation.env # Env vars (paths, whisper.cpp model, etc.)
│ │ └── README.md # Setup, usage, and hotkey configuration
│ │
│ ├── borg-backup/ # Example 2: Automated BorgBackup script
│ │ ├── backup.sh # Full-featured backup + prune + compact routine
│ │ ├── borg-backup.service # systemd unit for manual/triggered runs
│ │ ├── borg-backup.timer # Optional systemd timer for scheduled runs
│ │ ├── config/ # Module-local settings
│ │ │ └── borg-backup.env # Customizable variables (dirs, repo name, etc.)
│ │ └── README.md # Configuration and operational details
│ │
│ └── ... # Future automations (network monitor, sync tool, etc.)
│
├── staging/ # houses scripts that are being tested/staged to be moved into systemd automations
|
├── scripts/ # Shared or ad-hoc system utility scripts
│ ├── setup-hotkeys.sh # Registers or updates desktop hotkey triggers
│ ├── setup-services.sh # Enables/disables module-specific systemd units
│ ├── link-module.sh # Symlinks module units into ~/.config/systemd/user
│ └── utils.sh # Shared functions (logging, env validation, etc.)
│
└── docs/ # Developer documentation and standards
├── ARCHITECTURE_SUMMARY.md # Quick reference for architecture decisions
├── DICTATION_ARCHITECTURE.md # Detailed dictation module design
├── SYSTEM_PROFILE.md # System-specific configuration and recommendations
├── SETUP_CHECKLIST.md # Pre-flight validation and dependency setup
├── CONTRIBUTING.md # Conventions for adding and testing modules
└── ARCHITECTURE.md # Detailed design overview and reasoning


---

## 🧱 Repository Purpose

`systemd-automations` is designed to:

- Serve as a **single home** for automation scripts, services, and timers.
- Keep **modules decoupled** — each one works standalone or under systemd.
- Support **dynamic linking** — use `scripts/link-module.sh` to symlink services into your user systemd directory when ready.
- Encourage **clarity, reusability, and minimal coupling** between logic (scripts) and orchestration (systemd).

---

## 🗣️ Example Module: Dictation (Voice-to-Text)

This module adds a **local voice dictation utility** that records from the microphone, transcribes speech using faster-whisper AI, and pastes text into the active cursor position.

**System-Optimized:** Architecture has been tailored for **Manjaro Linux + XFCE + X11** based on comprehensive system detection.

**Key components:**
- `dictation.py` — Core recording and transcription logic (faster-whisper).
- `dictation-toggle.sh` — Wrapper script for hotkey integration.
- `config/dictation.env` — User-configurable settings (model, audio device, etc.).
- `setup.sh` — Automated dependency checking and XFCE hotkey registration.

**Example usage:**
Press `Ctrl+Alt+Space` → speak → press again → text appears at your cursor.

**Documentation:**
- 📋 [Quick Summary](docs/ARCHITECTURE_SUMMARY.md) - Key decisions and overview
- 🏗️ [Full Architecture](docs/DICTATION_ARCHITECTURE.md) - Technical deep-dive
- 🖥️ [System Profile](docs/SYSTEM_PROFILE.md) - Hardware/software inventory
- ✅ [Setup Checklist](docs/SETUP_CHECKLIST.md) - Pre-flight validation

---

## 💾 Example Module: Borg Backup Automation

A robust Borg-based backup pipeline with integrated logging, pruning, and repository compaction.  
Adapted from your current working script.

**Key components:**
- `backup.sh` — Orchestrates backup, prune, and compact phases with fault tolerance.
- `borg-backup.service` — Runs backups manually or via trigger.
- `borg-backup.timer` — Optional daily/weekly timer for scheduled jobs.
- `config/backup.env` — Define `$BACKUP_DIR`, `$BORG_REPO`, exclusions, etc.

**Example use:**
```bash
systemctl --user start borg-backup.service
systemctl --user enable borg-backup.timer
```

---


## 🧩 Extending the Repo

To add a new automation:

1. Create a directory:

   ```bash
   mkdir -p modules/my-automation/config
   ```
2. Add:

   * Core script (`my-automation.sh` or `.py`)
   * Optional `my-automation.service` / `.timer`
   * Config file under `config/`
   * `README.md` with usage and variables
3. Link it for systemd (when ready):

   ```bash
   ./scripts/link-module.sh modules/my-automation/my-automation.service
   systemctl --user daemon-reload
   systemctl --user enable my-automation.service
   ```

Each module remains **self-contained** and **independent** of others until explicitly coupled.

---

## 🧠 Design Principles

* **Local-first:** Automations run entirely on-device.
* **Decoupled:** Logic, configuration, and orchestration live in their own layers.
* **System-native:** Uses `systemd` for reliability and lifecycle management.
* **Composable:** Modules can be chained, triggered, or scheduled dynamically.
* **Transparent:** Scripts remain simple, auditable, and portable.

---

## 📦 Setup

```bash
git clone https://github.com/<your-username>/systemd-automations.git
cd systemd-automations
./scripts/setup-services.sh
```

You can now manage modules individually:

```bash
systemctl --user start dictation.service
systemctl --user enable borg-backup.timer
```

---

**Author:** Sidhant Dixit
**License:** MIT
**Version:** 0.0.1