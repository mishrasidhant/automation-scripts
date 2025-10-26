# Environment Setup Guide

This document explains how to configure environment variables for the automation-scripts project.

---

## Overview

To keep personal paths and usernames out of the public repository, this project uses environment variables. All documentation and scripts reference `$AUTOMATION_SCRIPTS_DIR` instead of hardcoded paths.

---

## Quick Setup

### 1. Set Environment Variable

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
export AUTOMATION_SCRIPTS_DIR="$HOME/path/to/automation-scripts"
```

**Example:**
```bash
export AUTOMATION_SCRIPTS_DIR="$HOME/Files/W/Workspace/git/automation-scripts"
```

### 2. Reload Shell

```bash
source ~/.bashrc
```

### 3. Verify

```bash
echo $AUTOMATION_SCRIPTS_DIR
# Should output your project path
```

---

## Alternative: Using .env File

The project includes a `.env` file (gitignored) for local configuration.

### 1. Source the .env file

```bash
cd $AUTOMATION_SCRIPTS_DIR
source .env
```

### 2. Verify

```bash
echo $AUTOMATION_SCRIPTS_DIR
```

**Note:** The `.env` file is local only and will not be committed to git.

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AUTOMATION_SCRIPTS_DIR` | Project root directory | `/home/user/automation-scripts` |
| `USER` | Current username | Automatically set by shell |
| `HOME` | User home directory | Automatically set by shell |

---

## Usage in Documentation

When you see `$AUTOMATION_SCRIPTS_DIR` in documentation:

```bash
# This command:
cd $AUTOMATION_SCRIPTS_DIR

# Expands to your actual path:
cd /home/your-username/path/to/automation-scripts
```

---

## Systemd Services

Systemd service files need absolute paths and don't expand shell variables. There are two approaches:

### Option 1: Direct Substitution

Create service files with your actual paths:

```ini
[Service]
ExecStart=/home/your-username/automation-scripts/.venv/bin/python \
          /home/your-username/automation-scripts/modules/dictation/dictate.py --start
```

### Option 2: Generator Script (Recommended)

Use a script to generate service files with substituted paths:

```bash
# Create a generator script
cat > scripts/generate-service.sh << 'EOF'
#!/bin/bash
# Generate systemd service file with actual paths

SERVICE_NAME="$1"
TEMPLATE_FILE="modules/$SERVICE_NAME/$SERVICE_NAME.service.template"
OUTPUT_FILE="$HOME/.config/systemd/user/$SERVICE_NAME.service"

# Substitute environment variables
envsubst < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"
systemctl --user daemon-reload
EOF

chmod +x scripts/generate-service.sh
```

**Service Template Example:**
```ini
# modules/dictation/dictation.service.template
[Unit]
Description=Voice Dictation Service

[Service]
Type=simple
ExecStart=${AUTOMATION_SCRIPTS_DIR}/.venv/bin/python \
          ${AUTOMATION_SCRIPTS_DIR}/modules/dictation/dictate.py --start
WorkingDirectory=${AUTOMATION_SCRIPTS_DIR}/modules/dictation
Environment="PATH=${AUTOMATION_SCRIPTS_DIR}/.venv/bin:/usr/bin"

[Install]
WantedBy=default.target
```

**Generate Service:**
```bash
# Set environment variable first
export AUTOMATION_SCRIPTS_DIR="/your/path/automation-scripts"

# Generate the service file
scripts/generate-service.sh dictation

# Enable and start
systemctl --user enable dictation.service
systemctl --user start dictation.service
```

---

## Scripts Behavior

All scripts in this project are designed to work with `$AUTOMATION_SCRIPTS_DIR`:

### setup-dev.sh

```bash
# Checks for $AUTOMATION_SCRIPTS_DIR first
# Falls back to auto-detection if not set
PROJECT_ROOT="${AUTOMATION_SCRIPTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
```

### Usage

```bash
# With environment variable set:
source $AUTOMATION_SCRIPTS_DIR/scripts/setup-dev.sh dictation

# Or from any directory:
cd $AUTOMATION_SCRIPTS_DIR
source scripts/setup-dev.sh dictation
```

---

## Troubleshooting

### Variable Not Set

**Problem:** `bash: cd: $AUTOMATION_SCRIPTS_DIR: No such file or directory`

**Solution:**
```bash
# Check if variable is set
echo $AUTOMATION_SCRIPTS_DIR

# If empty, set it:
export AUTOMATION_SCRIPTS_DIR="/your/actual/path"

# Make it permanent:
echo 'export AUTOMATION_SCRIPTS_DIR="/your/actual/path"' >> ~/.bashrc
source ~/.bashrc
```

### Variable Points to Wrong Location

**Problem:** Variable points to old location after moving project

**Solution:**
```bash
# Update in bashrc
nano ~/.bashrc
# Find and update the export line

# Reload
source ~/.bashrc

# Update .env file
nano $AUTOMATION_SCRIPTS_DIR/.env
```

### Scripts Can't Find Project Root

**Problem:** Scripts fail to locate files

**Solution:**
```bash
# Always run scripts from project root or use full path
cd $AUTOMATION_SCRIPTS_DIR
source scripts/setup-dev.sh dictation

# Or use absolute path
source $AUTOMATION_SCRIPTS_DIR/scripts/setup-dev.sh dictation
```

---

## Best Practices

### DO:
- ✅ Use `$AUTOMATION_SCRIPTS_DIR` in all scripts and documentation
- ✅ Set the variable in your shell profile for persistence
- ✅ Use relative paths when already in project directory
- ✅ Test scripts work with environment variable

### DON'T:
- ❌ Hardcode `/home/username/path` in scripts
- ❌ Commit `.env` with your actual paths
- ❌ Use absolute paths in systemd templates
- ❌ Assume everyone has the same directory structure

---

## For Contributors

If you're contributing to this project:

1. **Never commit personal paths**
   - Use `$AUTOMATION_SCRIPTS_DIR` in all documentation
   - Use `$USER` and `$HOME` for user-specific references

2. **Test with environment variables**
   ```bash
   # Unset to test auto-detection
   unset AUTOMATION_SCRIPTS_DIR
   
   # Scripts should still work from project root
   cd /path/to/project
   source scripts/setup-dev.sh
   ```

3. **Document new scripts**
   - Add environment variable usage to script headers
   - Update this guide if adding new variables

---

## Related Documentation

- `.env.example` - Environment variable template
- `README.md` - Project overview
- `scripts/setup-dev.sh` - Development environment setup

---

**Last Updated:** October 26, 2025  
**Maintained By:** Project Contributors

