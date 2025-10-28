# Dependency Management Architecture

**Version:** 2.0 (UV Migration)  
**Date:** October 28, 2025  
**Status:** Implemented  
**Architect:** Winston  
**Implementation:** v0.1.0

---

## Executive Summary

This document defines the dependency management strategy for the automation-scripts project, which houses multiple Python-based automation modules with varying dependency requirements. The architecture prioritizes reproducibility, fast installation, clear module boundaries, and operational simplicity.

**Key Decision (v2.0):** UV package management with src-layout and locked dependencies.

**Previous Approach (v1.0):** Project-level virtual environment with pip and requirements files.

**Migration Status:** ✅ Completed in v0.1.0 (October 2025)

---

## 🚀 UV Architecture (v2.0 - Current)

### Quick Reference

**Package Manager:** UV (Astral)  
**Package Structure:** src-layout  
**Configuration:** pyproject.toml + uv.lock  
**Installation Time:** < 1 second (cached), < 30 seconds (clean)

### Core Components

```
automation-scripts/
├── pyproject.toml              # Project definition (PEP 621)
├── uv.lock                     # Locked dependencies with hashes
├── src/automation_scripts/     # Src-layout package structure
│   └── dictation/
│       ├── __init__.py
│       ├── __main__.py
│       ├── dictate.py
│       ├── config.py           # TOML configuration
│       └── constants.py        # XDG paths
└── config/
    └── dictation.toml.example  # Example configuration
```

### Key Commands

```bash
# Install dependencies
uv sync --extra dictation

# Run module
uv run dictation-toggle --start

# Development
uv sync --group dev --extra dictation
uv run pytest
```

### Benefits Over Previous Approach

| Aspect | v1.0 (pip/venv) | v2.0 (UV) |
|--------|-----------------|-----------|
| Installation | 5-10 minutes | < 30 seconds |
| Reproducibility | Variable | 100% locked |
| Activation | Manual `source` | Automatic |
| Dependency Resolution | Manual | Automatic |
| Lock File | None | uv.lock with hashes |

### Migration

See [docs/MIGRATION-TO-UV.md](../MIGRATION-TO-UV.md) for complete migration guide from v1.0 to v2.0.

---

## Table of Contents

1. [Context & Requirements](#context--requirements)
2. [Architectural Decision](#architectural-decision)
3. [System Architecture](#system-architecture)
4. [Directory Structure](#directory-structure)
5. [Requirements Organization](#requirements-organization)
6. [Development Workflow](#development-workflow)
7. [Production Integration](#production-integration)
8. [Trade-offs & Alternatives](#trade-offs--alternatives)
9. [Migration Strategy](#migration-strategy)
10. [Future Considerations](#future-considerations)

**Note:** Sections below describe the v1.0 architecture (pip/venv) for historical reference. Current implementation uses UV (v2.0) as described above.

---

## Context & Requirements

### Project Profile

**Type:** Personal automation scripts collection  
**Scope:** Multiple independent automation modules  
**Environment:** Manjaro Linux (Arch-based)  
**Constraint:** PEP 668 externally-managed-environment

### Current State

- Multiple automation modules planned (dictation, backup, monitoring, etc.)
- Each module has distinct dependencies
- System Python is externally managed (Arch/Manjaro policy)
- Some modules will run as systemd services
- Development and production use the same system

### Requirements

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| R1 | Isolate from system packages | CRITICAL | Avoid polluting system Python per PEP 668 |
| R2 | Support multiple modules with different deps | HIGH | Project will grow beyond dictation |
| R3 | Simple activation for development | HIGH | Developer experience |
| R4 | Clear dependency tracking per module | MEDIUM | Maintenance and documentation |
| R5 | Work with systemd services | HIGH | Production deployment |
| R6 | Handle shared dependencies efficiently | MEDIUM | Avoid duplication where possible |
| R7 | Support incremental module installation | MEDIUM | Don't install all deps for one module |
| R8 | No root/sudo for normal operations | HIGH | Security best practice |

### Constraints

- **Platform:** Arch/Manjaro Linux (PEP 668 enforced)
- **Python:** 3.13.7 (system Python)
- **Package Manager:** pacman (system), pip (within venv)
- **Deployment:** Systemd user services
- **Team Size:** Single developer (personal automation)

---

## Architectural Decision

### Selected Approach: Project-Level Virtual Environment

**Decision:** Use a single virtual environment at the project root with modular requirements files organized by module.

**Architecture Pattern:** Monorepo with Shared Runtime Environment

**Rationale:**
1. **Simplicity:** One activation command for entire project
2. **Isolation:** Complete separation from system packages
3. **Modularity:** Clear dependency tracking per module
4. **Efficiency:** Shared dependencies installed once
5. **Integration:** Single path for systemd services
6. **Scalability:** Handles 5-20 automation modules effectively

### Non-Goals

- ❌ Universal package distribution (not building pip packages)
- ❌ Multi-version Python support (system Python only)
- ❌ Docker/container deployment (native systemd)
- ❌ Enterprise-scale dependency management
- ❌ Dependency conflict resolution between modules (acceptable risk)

---

## System Architecture

### High-Level View

```
┌─────────────────────────────────────────────────────────────┐
│                    automation-scripts                       │
│                   (Project Repository)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│  .venv/      │◄─────────────│ requirements/│
│  (Python     │  references  │  (Dependency │
│   runtime)   │              │   manifests) │
└──────┬───────┘              └──────┬───────┘
       │                             │
       │ provides runtime            │ declares deps
       │                             │
       ▼                             ▼
┌─────────────────────────────────────────────┐
│            modules/                         │
│  ┌───────────┐  ┌───────────┐             │
│  │ dictation │  │  backup   │   (future)  │
│  └───────────┘  └───────────┘             │
└─────────────────────────────────────────────┘
       │                     │
       │ executed by         │
       ▼                     ▼
┌─────────────────────────────────────────────┐
│          systemd user services              │
│  (references .venv/bin/python)              │
└─────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Lifecycle |
|-----------|---------------|-----------|
| `.venv/` | Python runtime isolation | Created once, updated as needed |
| `requirements/` | Dependency declarations | Version controlled, static |
| `modules/*/` | Automation logic | Independent, loosely coupled |
| `setup-dev.sh` | Environment activation | Run at session start |
| `install-module.sh` | Selective dependency installation | Run per module as needed |

---

## Directory Structure

### Complete Layout

```
automation-scripts/
├── .venv/                              # Python virtual environment
│   ├── bin/
│   │   ├── python                      # Python 3.13.7 (isolated)
│   │   ├── pip                         # Pip for this venv
│   │   └── activate                    # Manual activation script
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/          # Installed packages
│   └── pyvenv.cfg                      # Venv configuration
│
├── requirements/                       # Dependency manifests
│   ├── README.md                       # Documentation for this directory
│   ├── base.txt                        # Shared/common dependencies
│   ├── dictation.txt                   # Dictation module deps
│   ├── backup.txt                      # Backup module deps (future)
│   ├── monitoring.txt                  # Monitoring deps (future)
│   ├── dev.txt                         # Development tools
│   └── all.txt                         # Complete installation
│
├── scripts/                            # Helper scripts
│   ├── setup-dev.sh                    # Smart venv activation
│   ├── install-module.sh               # Install specific module deps
│   ├── install-system-deps.sh          # System package installation
│   └── verify-deps.sh                  # Dependency validation
│
├── modules/                            # Automation modules
│   ├── dictation/
│   │   ├── dictate.py
│   │   ├── test_dictate.py
│   │   ├── README.md                   # Documents dependencies
│   │   └── DEPENDENCIES.txt            # Points to requirements/dictation.txt
│   │
│   ├── backup/                         # Future module
│   │   ├── backup-manager.py
│   │   └── DEPENDENCIES.txt
│   │
│   └── common/                         # Shared code (if needed)
│       └── utils.py
│
├── docs/
│   ├── architecture/
│   │   ├── dependency-management.md    # This document
│   │   ├── SYSTEM_DEPS.md              # System package requirements
│   │   └── ...
│   └── ...
│
├── .gitignore                          # Excludes .venv/
├── README.md                           # Project overview
└── pyproject.toml                      # Optional: Project metadata

```

### File Ownership

| Path | Owner | Purpose |
|------|-------|---------|
| `.venv/` | Developer | Runtime isolation (not in git) |
| `requirements/` | Version Control | Dependency declarations |
| `scripts/` | Version Control | Tooling |
| `modules/` | Version Control | Application code |

---

## Requirements Organization

### File Structure Rationale

#### `requirements/base.txt`
**Purpose:** Minimal shared dependencies across all modules  
**Contents:** Usually empty or very minimal for personal automation

```txt
# Shared dependencies (if any)
# Keep this minimal - only truly shared libs
# Examples:
# - logging libraries
# - config parsers (if standardized)
# - custom common utilities
```

**Principle:** Base should be truly universal, not a dumping ground.

---

#### `requirements/dictation.txt`
**Purpose:** Dependencies for voice dictation module  
**Contents:** Audio, transcription, and text injection dependencies

```txt
# Audio recording and manipulation
sounddevice>=0.4.6      # Python audio I/O
numpy>=1.24.0           # Audio data arrays

# Speech recognition
faster-whisper>=0.10.0  # Optimized Whisper transcription

# Include base requirements
-r base.txt
```

**Versioning Strategy:**
- Use `>=` for flexibility (personal project)
- Pin major versions to avoid breaking changes
- Document known working versions in module README

---

#### `requirements/backup.txt` (Future Example)
**Purpose:** Dependencies for backup automation module

```txt
# Backup and compression
python-borgbackup>=1.2.0  # Borg backup Python API (if available)
# Or just rely on system borg command

# Cloud storage (optional)
# boto3>=1.28.0           # AWS S3 integration
# paramiko>=3.3.0         # SFTP/SSH

-r base.txt
```

---

#### `requirements/dev.txt`
**Purpose:** Development and testing tools

```txt
# Testing frameworks
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Code quality
black>=23.0.0           # Code formatter
flake8>=6.0.0           # Linter
mypy>=1.5.0             # Type checker
isort>=5.12.0           # Import sorter

# Development utilities
ipython>=8.15.0         # Enhanced REPL
pdbpp>=0.10.3           # Better debugger

# Include all module dependencies for comprehensive testing
-r all.txt
```

**Usage:** Only installed when actively developing/testing.

---

#### `requirements/all.txt`
**Purpose:** Install all module dependencies in one command

```txt
# Complete installation of all modules
# Useful for:
# - Full project setup
# - CI/CD environments
# - Testing interactions between modules

-r dictation.txt
-r backup.txt
-r monitoring.txt
# Add new modules here
```

---

### Dependency Declaration Guidelines

**DO:**
- ✅ Use specific feature requirements (`sounddevice>=0.4.6`)
- ✅ Document why each dependency exists (comments)
- ✅ Group related dependencies together
- ✅ Include `-r base.txt` in module requirements
- ✅ Pin major versions for stability

**DON'T:**
- ❌ Add dependencies "just in case" they might be useful
- ❌ Use exact pins (`==`) unless absolutely necessary
- ❌ Mix development and production dependencies
- ❌ Duplicate base requirements in module files
- ❌ Add system package names (those go in docs)

---

## Development Workflow

### Setup & Activation

#### Initial Setup (One-Time)

```bash
# 1. Clone repository
cd $HOME/Files/W/Workspace/git/automation/automation-scripts

# 2. Install system dependencies (requires sudo)
sudo pacman -S portaudio xdotool  # Dictation module requirements
# See docs/architecture/SYSTEM_DEPS.md for complete list

# 3. Create and activate virtual environment
source scripts/setup-dev.sh

# 4. Install dependencies for module you're working on
source scripts/setup-dev.sh dictation
# Or install everything:
source scripts/setup-dev.sh all
```

#### Daily Development

```bash
# Start development session
cd automation-scripts
source scripts/setup-dev.sh

# Your venv is now active
# Prompt shows: (.venv) [user@host automation-scripts]$

# Work on specific module
cd modules/dictation
python dictate.py --start

# Run tests
python test_dictate.py

# When done
deactivate
```

---

### Adding New Module Dependencies

**Scenario:** Adding a new automation module (e.g., "monitoring")

```bash
# 1. Create requirements file
cat > requirements/monitoring.txt << 'EOF'
# System monitoring dependencies
psutil>=5.9.0           # CPU, memory, disk stats
requests>=2.31.0        # HTTP for webhooks

-r base.txt
EOF

# 2. Update requirements/all.txt
echo "-r monitoring.txt" >> requirements/all.txt

# 3. Create module structure
mkdir -p modules/monitoring
touch modules/monitoring/DEPENDENCIES.txt

# 4. Document dependencies
echo "requirements/monitoring.txt" > modules/monitoring/DEPENDENCIES.txt

# 5. Install new dependencies
source scripts/setup-dev.sh monitoring
```

---

### Installing Dependencies Selectively

```bash
# Option 1: Using setup-dev.sh (recommended)
source scripts/setup-dev.sh dictation

# Option 2: Manual installation
source .venv/bin/activate
pip install -r requirements/dictation.txt

# Option 3: Install specific package
source .venv/bin/activate
pip install faster-whisper
```

---

### Updating Dependencies

```bash
# Update all installed packages
source .venv/bin/activate
pip list --outdated
pip install --upgrade sounddevice faster-whisper

# Freeze current state (documentation only)
pip freeze > docs/known-working-versions.txt
```

**Philosophy:** Don't obsess over updates for personal automation. Update when:
- Security vulnerability announced
- Need specific new feature
- Encountering bugs fixed in newer version

---

## Production Integration

### Systemd Service Configuration

Systemd services reference the project virtual environment directly.

#### Example: Dictation Service

```ini
[Unit]
Description=Voice Dictation Recording Service
After=pulseaudio.service

[Service]
Type=simple
# Use venv Python explicitly
ExecStart=$HOME/Files/W/Workspace/git/automation/automation-scripts/.venv/bin/python \
          $HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation/dictate.py \
          --start

# Ensure venv is in PATH
Environment="PATH=$HOME/.../automation-scripts/.venv/bin:/usr/local/bin:/usr/bin"

# Set working directory
WorkingDirectory=$HOME/Files/W/Workspace/git/automation/automation-scripts/modules/dictation

# User context
User=%u
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=default.target
```

**Key Points:**
- ✅ Absolute path to venv Python
- ✅ Environment PATH includes venv
- ✅ No sudo/root required
- ✅ Proper working directory

---

### Service Installation Script

Create helper scripts for service management:

```bash
# scripts/install-service.sh
#!/bin/bash
# Install systemd user service

MODULE="$1"
if [ -z "$MODULE" ]; then
    echo "Usage: $0 <module-name>"
    exit 1
fi

SERVICE_FILE="modules/$MODULE/$MODULE.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Service file not found: $SERVICE_FILE"
    exit 1
fi

# Copy to systemd user directory
cp "$SERVICE_FILE" ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable "$MODULE.service"

echo "Service installed: $MODULE.service"
echo "Start with: systemctl --user start $MODULE.service"
```

---

### Wrapper Scripts (Alternative)

For modules that don't run as services:

```bash
#!/bin/bash
# modules/dictation/dictate-wrapper.sh
# Wrapper that activates venv and runs dictate.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# Check venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found"
    echo "Run: source scripts/setup-dev.sh dictation"
    exit 1
fi

# Execute with venv Python
exec "$VENV_PYTHON" "$SCRIPT_DIR/dictate.py" "$@"
```

**Usage:**
```bash
# XFCE hotkey calls wrapper directly
/path/to/modules/dictation/dictate-wrapper.sh --start
```

**Benefits:**
- No need to activate venv manually
- Proper error messages if venv missing
- Can be called from any context (cron, hotkeys, etc.)

---

## Trade-offs & Alternatives

### Decision Matrix

| Approach | Isolation | Simplicity | Dep Conflicts | Systemd Integration | Verdict |
|----------|-----------|------------|---------------|---------------------|---------|
| **Project-level venv** ✅ | High | High | Medium risk | Easy | **SELECTED** |
| Per-module venvs | Highest | Low | No risk | Complex | Overkill |
| System packages | None | Highest | High risk | Easiest | Violates PEP 668 |
| Docker containers | Highest | Low | No risk | Medium | Too heavy |
| pipx per module | High | Medium | No risk | Complex | Not designed for this |

---

### Alternative: Per-Module Virtual Environments

**Structure:**
```
modules/
├── dictation/
│   ├── .venv/
│   └── dictate.py
└── backup/
    ├── .venv/
    └── backup-manager.py
```

**Pros:**
- Perfect dependency isolation
- No risk of conflicts between modules
- Clear ownership boundaries

**Cons:**
- Multiple activation commands (confusing)
- Duplicate dependencies (numpy in multiple venvs)
- Complex systemd configuration (which venv?)
- Harder to test module interactions
- More disk space usage

**Verdict:** Overkill for personal automation with 5-20 modules.

---

### Alternative: System Packages via pacman

**Approach:** Use `--break-system-packages` or `sudo pacman -S python-*`

**Pros:**
- Simplest possible setup
- No venv management
- Works everywhere instantly

**Cons:**
- ❌ Violates PEP 668 (intentionally breaking guarantees)
- ❌ Pollutes system Python namespace
- ❌ Conflicts with system updates
- ❌ Harder to track what you installed
- ❌ May break system tools that depend on specific versions

**Verdict:** Unacceptable. This is explicitly what PEP 668 prevents.

---

### Alternative: Docker Containers

**Approach:** Each module runs in its own container

**Pros:**
- Complete isolation (OS-level)
- Reproducible environments
- No dependency conflicts possible

**Cons:**
- Heavy overhead for simple scripts
- Complex systemd integration
- Harder development workflow
- Audio/desktop integration challenges (dictation needs mic/notifications)
- Overkill for automation scripts

**Verdict:** Too complex for personal automation. Consider if distributing to others.

---

## Migration Strategy

### Phase 1: Setup Foundation (Current)

**Timeline:** 1 hour

```bash
# 1. Create requirements directory
mkdir -p requirements

# 2. Create base requirements
touch requirements/base.txt

# 3. Create module requirements
cat > requirements/dictation.txt << 'EOF'
sounddevice>=0.4.6
numpy>=1.24.0
faster-whisper>=0.10.0
-r base.txt
EOF

# 4. Create combined requirements
cat > requirements/all.txt << 'EOF'
-r dictation.txt
EOF

# 5. Create dev requirements
cat > requirements/dev.txt << 'EOF'
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
-r all.txt
EOF
```

---

### Phase 2: Create Tooling

**Timeline:** 30 minutes

Create helper scripts in `scripts/`:

1. `setup-dev.sh` - Smart venv activation with module selection
2. `install-system-deps.sh` - System package installation guide
3. `verify-deps.sh` - Dependency validation

---

### Phase 3: Setup Virtual Environment

**Timeline:** 15 minutes

```bash
# Create venv
python3 -m venv .venv

# Activate and upgrade pip
source .venv/bin/activate
pip install --upgrade pip

# Install dictation dependencies (for Story 1)
pip install -r requirements/dictation.txt

# Verify
python -c "import sounddevice; print('✓ sounddevice')"
python -c "import numpy; print('✓ numpy')"
```

---

### Phase 4: Update Documentation

**Timeline:** 30 minutes

Update existing documentation to reference new structure:

1. Module READMEs (reference requirements/module.txt)
2. Main README (setup instructions)
3. Story documentation (dev environment setup)
4. Manual testing guides (use venv)

---

### Phase 5: Cleanup

**Timeline:** 15 minutes

```bash
# Remove old activation script (replaced by setup-dev.sh)
rm activate-dev.sh

# Update .gitignore
cat >> .gitignore << 'EOF'

# Virtual environment
.venv/
venv/
ENV/
env/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
EOF

# Commit changes
git add requirements/ scripts/ .gitignore docs/architecture/
git commit -m "architecture: implement dependency management strategy"
```

---

## Future Considerations

### Scaling Beyond 20 Modules

**Indicators this architecture needs revision:**
- 20+ automation modules
- Frequent dependency conflicts between modules
- Need for different Python versions per module
- Distributing modules to other users
- Complex integration testing requirements

**Next Architecture:** Consider workspace tools like:
- Poetry workspaces
- Pants build system
- Bazel (overkill, but mentioned for completeness)

---

### Adding Shared Library Code

**Scenario:** Multiple modules need common functionality

**Solution:** Create `modules/common/` package

```python
# modules/common/__init__.py
"""Shared utilities for automation modules"""

# modules/common/notifications.py
def send_notification(title, message, urgency="normal"):
    """Shared notification logic"""
    ...

# modules/dictation/dictate.py
from common.notifications import send_notification
```

**Requirements:**
```txt
# requirements/base.txt (if common uses external deps)
# Otherwise, keep base.txt empty
```

**Note:** Common code has no external dependencies initially. Add to base.txt only if genuinely shared.

---

### Python Version Upgrades

**Scenario:** System Python upgrades from 3.13 to 3.14

**Impact:** Virtual environment may break (compiled extensions)

**Solution:**
```bash
# Remove old venv
rm -rf .venv

# Recreate with new Python
python3 -m venv .venv
source .venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements/all.txt

# Test all modules
pytest modules/
```

**Frequency:** Arch upgrades Python ~1-2x per year. Budget 15 minutes for recreation.

---

### Adding Type Checking

**Future Enhancement:** Full type coverage with mypy

```bash
# requirements/dev.txt (already includes mypy)

# mypy.ini (project root)
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

# Per-module configuration
[mypy-modules.dictation.*]
ignore_missing_imports = True
```

---

### CI/CD Integration (Future)

**Scenario:** Add automated testing (GitHub Actions, GitLab CI)

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install system dependencies
        run: sudo apt-get install -y portaudio19-dev
      
      - name: Create venv and install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements/dev.txt
      
      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest modules/ -v
      
      - name: Run linters
        run: |
          source .venv/bin/activate
          black --check modules/
          flake8 modules/
```

---

## Appendix

### Quick Reference

**Setup:**
```bash
source scripts/setup-dev.sh [module|all|dev]
```

**Install module dependencies:**
```bash
source scripts/setup-dev.sh dictation
```

**Run tests:**
```bash
cd modules/dictation && python test_dictate.py
```

**Update dependencies:**
```bash
source .venv/bin/activate
pip install --upgrade <package>
```

**Deactivate:**
```bash
deactivate
```

---

### System Dependencies Documentation

Create `docs/architecture/SYSTEM_DEPS.md`:

```markdown
# System Dependencies

Required system packages (installed via pacman):

## Dictation Module
- portaudio - Audio I/O library
- xdotool - X11 automation (text injection)

## Backup Module (Future)
- rsync - File synchronization
- borgbackup - Backup tool

## Installation

```bash
# Dictation
sudo pacman -S portaudio xdotool

# All modules
sudo pacman -S portaudio xdotool rsync borgbackup
```
```

---

### Glossary

| Term | Definition |
|------|------------|
| **Virtual Environment (venv)** | Isolated Python runtime with its own site-packages |
| **PEP 668** | Python Enhancement Proposal for externally managed environments |
| **Requirements File** | Text file listing pip packages and versions |
| **Project-level venv** | Single venv shared by all modules in a project |
| **Module** | Independent automation script/package within the project |
| **Site-packages** | Directory where pip installs packages |
| **Systemd User Service** | Background service running as the user (not root) |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-26 | Winston | Initial architecture document |

---

## Approval & Review

**Status:** Proposed  
**Requires Approval:** User  
**Implementation:** Pending approval

**Next Steps:**
1. Review and approve architecture
2. Create directory structure
3. Migrate dictation module to new structure
4. Create helper scripts
5. Update documentation
6. Test with manual workflow

---

**Document maintained by:** Winston (Architect)  
**Questions/Feedback:** Update this document with decisions and lessons learned

