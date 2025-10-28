# Development Guide

This guide is for developers who want to contribute to the dictation module or understand its internals.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Code Style and Linting](#code-style-and-linting)
- [Debugging](#debugging)
- [Adding New Features](#adding-new-features)
- [Release Process](#release-process)
- [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

**System dependencies**:
```bash
# Arch/Manjaro
sudo pacman -S portaudio xdotool libnotify git

# Ubuntu/Debian
sudo apt install portaudio19-dev xdotool libnotify-bin git

# Fedora
sudo dnf install portaudio-devel xdotool libnotify git
```

**UV package manager**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Clone Repository

```bash
git clone https://github.com/mishrasidhant/automation-scripts.git
cd automation-scripts
```

### Setup Development Environment

```bash
# Install all dependencies including dev tools
uv sync --extra dictation --group dev

# Verify installation
uv run pytest --version
uv run ruff --version
```

### Verify Setup

```bash
# Run tests
uv run pytest

# Check imports
uv run python -c "import automation_scripts.dictation; print('OK')"

# Try dictation (manual test)
uv run dictation-toggle --start
# Speak something
uv run dictation-toggle --stop
```

## Project Structure

### Source Code Layout

```
automation-scripts/
├── src/
│   └── automation_scripts/
│       ├── __init__.py               # Package root
│       └── dictation/                # Dictation module
│           ├── __init__.py           # Module entry point, main()
│           ├── __main__.py           # CLI entry point
│           ├── config.py             # Configuration loading and validation
│           ├── constants.py          # XDG paths and default values
│           └── dictate.py            # Core dictation logic
│
├── scripts/
│   ├── dictation-toggle.sh           # Shell wrapper for state management
│   ├── install-hotkey-service.sh     # Service installer
│   ├── register-hotkey.sh            # Hotkey registration
│   ├── unregister-hotkey.sh          # Hotkey removal
│   └── check-hotkey-status.sh        # Diagnostic tool
│
├── systemd/
│   └── dictation-hotkey.service      # Systemd user service
│
├── config/
│   ├── dictation.toml.example        # Full configuration example
│   ├── dictation-minimal.toml        # Minimal config
│   ├── dictation-performance.toml    # Performance-optimized
│   └── dictation-accuracy.toml       # Accuracy-optimized
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_config.py                # Configuration tests
│   ├── test_constants.py             # Constants and paths tests
│   └── README.md                     # Testing guide
│
├── docs/
│   ├── README.md                     # Main documentation
│   ├── ARCHITECTURE.md               # System design
│   ├── USER-GUIDE.md                 # User documentation
│   ├── TROUBLESHOOTING.md            # Problem solving
│   ├── DEVELOPMENT.md                # This file
│   ├── MIGRATION-TO-UV.md            # Migration guide
│   └── stories/                      # Implementation stories
│
├── pyproject.toml                    # UV project configuration
├── uv.lock                           # Dependency lock file
├── CHANGELOG.md                      # Version history
└── README.md                         # Repository overview
```

### Key Files and Their Purpose

**`src/automation_scripts/dictation/config.py`**:
- Loads configuration from TOML files
- Applies environment variable overrides
- Validates all configuration values
- **Add new config options here**

**`src/automation_scripts/dictation/constants.py`**:
- Defines XDG-compliant paths
- Contains all default values
- Maps environment variables to config keys
- **Add new constants here**

**`src/automation_scripts/dictation/dictate.py`**:
- Core dictation functionality
- Audio recording with sounddevice
- Whisper transcription with faster-whisper
- Text injection with xdotool
- **Add new features here**

**`scripts/dictation-toggle.sh`**:
- State management (lock files)
- UV environment activation
- Logging and error handling
- **Modify for new state transitions**

**`systemd/dictation-hotkey.service`**:
- Ensures hotkey persistence
- Registers on user login
- **Modify for service-level changes**

## Running Tests

### Basic Test Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_config.py

# Run specific test
uv run pytest tests/test_config.py::test_load_config_with_missing_file_uses_defaults
```

### Test Coverage

```bash
# Generate coverage report
uv run pytest --cov

# Generate HTML coverage report
uv run pytest --cov --cov-report=html
xdg-open htmlcov/index.html

# Show missing lines
uv run pytest --cov --cov-report=term-missing
```

### Test Categories

**Unit tests** (fast, no hardware):
```bash
uv run pytest -m "not integration"
```

**Integration tests** (require hardware):
```bash
uv run pytest -m integration
```

### Writing New Tests

**Location**: `tests/test_<module>.py`

**Structure**:
```python
def test_something_specific(fixture_name):
    """Test that something behaves correctly."""
    # Arrange: Set up test data
    config = {'whisper': {'model': 'tiny.en'}}
    
    # Act: Perform the action
    result = some_function(config)
    
    # Assert: Check the results
    assert result == expected_value
```

**Use fixtures**:
```python
def test_with_temp_config(tmp_config_file):
    """Test configuration loading."""
    config_path = tmp_config_file('''
        [whisper]
        model = "tiny.en"
    ''')
    cfg = load_config(config_path)
    assert cfg['whisper']['model'] == 'tiny.en'
```

**Test naming**:
- Descriptive: `test_load_config_with_invalid_toml_raises_error`
- Not: `test_config`, `test_load`, `test1`

See [tests/README.md](../tests/README.md) for complete testing guide.

## Code Style and Linting

### Linting with Ruff

```bash
# Check all source files
uv run ruff check src/

# Check specific file
uv run ruff check src/automation_scripts/dictation/config.py

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

### Code Style Guidelines

**Python (PEP 8)**:
- Line length: 100 characters (configured in pyproject.toml)
- Indentation: 4 spaces
- Imports: Grouped (stdlib, third-party, local)
- Docstrings: Google style

**Example**:
```python
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib

from .constants import CONFIG_FILE, DEFAULT_CONFIG


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from TOML file with environment overrides.
    
    Args:
        config_path: Optional path to TOML file
        
    Returns:
        Merged configuration dictionary
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Implementation...
    pass
```

**Shell scripts**:
- Use `#!/usr/bin/env bash`
- Add error handling: `set -euo pipefail`
- Use meaningful variable names
- Add comments for complex sections

**Example**:
```bash
#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/dictation.lock"

# Check if recording is in progress
if [[ -f "$LOCK_FILE" ]]; then
    echo "Recording already in progress"
    exit 1
fi

# Start recording...
```

### Type Checking

```bash
# Run mypy (optional, not enforced)
uv run mypy src/automation_scripts/dictation/
```

**Note**: Type checking is lenient (`disallow_untyped_defs = false`). Improve gradually.

## Debugging

### Debug Logging

**Enable verbose logging**:
```bash
export DICTATION_DEBUG=1
uv run dictation-toggle --start
```

**View logs in real-time**:
```bash
tail -f /tmp/dictation-toggle.log
```

**View systemd logs**:
```bash
journalctl --user -u dictation-hotkey.service -f
```

### Python Debugger

**Add breakpoint**:
```python
def some_function():
    import pdb; pdb.set_trace()  # Debugger will stop here
    # Continue execution...
```

**Run with debugger**:
```bash
uv run python -m pdb -m automation_scripts.dictation
```

### Debugging Tests

**Show print statements**:
```bash
uv run pytest -s
```

**Drop into debugger on failure**:
```bash
uv run pytest --pdb
```

**Show local variables**:
```bash
uv run pytest -l
```

### Testing Signal Handling

**Test SIGTERM handling**:
```bash
# Start recording
uv run dictation-toggle --start

# Get PID from lock file
PID=$(cat /tmp/dictation.lock | cut -d: -f1)

# Send SIGTERM
kill -TERM $PID

# Check cleanup happened
ls /tmp/dictation.lock  # Should not exist
```

### Mock Audio Devices

**For testing without microphone**:
```python
import pytest
from unittest.mock import patch

@pytest.mark.integration
def test_audio_recording(monkeypatch):
    """Test audio recording with mocked device."""
    # Mock sounddevice to avoid needing real microphone
    with patch('sounddevice.InputStream'):
        result = record_audio()
        assert result is not None
```

## Adding New Features

### Adding a Configuration Option

**1. Add constant** (`constants.py`):
```python
# Add default value
DEFAULT_NEW_OPTION = 'default_value'

# Add to DEFAULT_CONFIG
DEFAULT_CONFIG = {
    'section_name': {
        'new_option': DEFAULT_NEW_OPTION,
    },
}

# Add to ENV_VAR_MAPPING
ENV_VAR_MAPPING = {
    f'{ENV_VAR_PREFIX}NEW_OPTION': ('section_name', 'new_option'),
}
```

**2. Add validation** (`config.py`):
```python
def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration values."""
    # ... existing validation ...
    
    # Validate new option
    new_option = config.get('section_name', {}).get('new_option', '')
    if new_option and new_option not in VALID_OPTIONS:
        errors.append(
            f"Invalid new_option '{new_option}'. "
            f"Valid options: {', '.join(VALID_OPTIONS)}"
        )
```

**3. Update example config** (`config/dictation.toml.example`):
```toml
[section_name]
# Description of new option
# Options: value1, value2, value3
# Default: default_value
new_option = "default_value"
```

**4. Write tests** (`tests/test_config.py`):
```python
def test_new_option_validation(sample_config):
    """Test validation of new option."""
    sample_config['section_name']['new_option'] = 'invalid'
    
    with pytest.raises(ConfigurationError):
        validate_config(sample_config)

def test_new_option_env_override(sample_config, env_override):
    """Test environment variable override for new option."""
    env_override('DICTATION_NEW_OPTION', 'value1')
    
    cfg = apply_env_overrides(sample_config.copy())
    assert cfg['section_name']['new_option'] == 'value1'
```

**5. Update documentation**:
- Add to [USER-GUIDE.md](USER-GUIDE.md) in "Customizing Behavior" section
- Update [ARCHITECTURE.md](ARCHITECTURE.md) if architectural impact
- Mention in [CHANGELOG.md](../CHANGELOG.md)

### Adding a New Function

**1. Write function with docstring**:
```python
def new_feature(param: str) -> bool:
    """
    Brief description of what function does.
    
    Detailed explanation of behavior, edge cases, etc.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
    # Implementation
    return True
```

**2. Write tests first (TDD)**:
```python
def test_new_feature_success():
    """Test new feature with valid input."""
    result = new_feature("valid")
    assert result is True

def test_new_feature_failure():
    """Test new feature with invalid input."""
    with pytest.raises(ValueError):
        new_feature("invalid")
```

**3. Run tests**:
```bash
uv run pytest tests/test_dictate.py::test_new_feature_success -v
```

**4. Implement until tests pass**

**5. Check coverage**:
```bash
uv run pytest --cov=automation_scripts.dictation.dictate tests/test_dictate.py
```

### Adding a Script

**1. Create script**:
```bash
touch scripts/new-script.sh
chmod +x scripts/new-script.sh
```

**2. Add header**:
```bash
#!/usr/bin/env bash
#
# Brief description of script
#
# Usage: ./scripts/new-script.sh [options]

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Functions
main() {
    # Implementation
    echo "Script working"
}

# Run main
main "$@"
```

**3. Test script**:
```bash
./scripts/new-script.sh
```

**4. Document in README or USER-GUIDE**

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes (e.g., v1.0.0 → v2.0.0)
- **MINOR**: New features, backward compatible (e.g., v0.1.0 → v0.2.0)
- **PATCH**: Bug fixes (e.g., v0.1.0 → v0.1.1)

### Release Checklist

**1. Update version**:
```toml
# pyproject.toml
[project]
version = "0.2.0"
```

**2. Update CHANGELOG.md**:
```markdown
## [0.2.0] - 2025-11-01

### Added
- New feature X
- Configuration option Y

### Changed
- Improved performance of Z

### Fixed
- Bug in transcription for special characters
```

**3. Run full test suite**:
```bash
uv run pytest
uv run pytest --cov
```

**4. Test installation from scratch**:
```bash
# In fresh clone or different machine
git clone <repo>
cd automation-scripts
uv sync --extra dictation
./scripts/install-hotkey-service.sh
# Test functionality
```

**5. Update documentation**:
- Ensure all docs reflect new version
- Update README.md if needed
- Check all links work

**6. Create git tag**:
```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

**7. Create GitHub release**:
- Go to GitHub Releases
- Create new release from tag
- Copy CHANGELOG.md content
- Add any additional notes

## Contributing Guidelines

### Before Contributing

1. **Check existing issues**: Avoid duplicates
2. **Discuss major changes**: Open an issue first
3. **Read this guide**: Understand project structure
4. **Setup dev environment**: Follow setup instructions

### Contribution Workflow

**1. Fork and clone**:
```bash
git clone https://github.com/yourusername/automation-scripts.git
cd automation-scripts
git remote add upstream https://github.com/mishrasidhant/automation-scripts.git
```

**2. Create feature branch**:
```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/bug-description
```

**3. Make changes**:
- Write code
- Add tests
- Update documentation

**4. Test thoroughly**:
```bash
uv run pytest
uv run ruff check src/
```

**5. Commit with clear messages**:
```bash
git add .
git commit -m "Add feature: short description

Detailed explanation of what changed and why.

Fixes #123"
```

**6. Keep up to date**:
```bash
git fetch upstream
git rebase upstream/main
```

**7. Push and create PR**:
```bash
git push origin feature/my-new-feature
```
Then create Pull Request on GitHub.

### Pull Request Guidelines

**Title**: Clear, descriptive
- Good: "Add GPU support for faster transcription"
- Bad: "Update code", "Fix"

**Description**: Include:
- What changed and why
- How to test
- Screenshots (if UI changes)
- Breaking changes (if any)
- Related issues

**Checklist**:
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Commits are clean and clear
- [ ] No merge conflicts

### Code Review Process

**Reviewers will check**:
- Functionality: Does it work as intended?
- Tests: Are there adequate tests?
- Code quality: Is it clean and maintainable?
- Documentation: Is it documented?
- Style: Does it follow conventions?

**Be patient**: Reviews take time
**Be responsive**: Address feedback promptly
**Be respectful**: Constructive discussion only

### What to Contribute

**Welcome contributions**:
- Bug fixes
- New features (discussed first)
- Documentation improvements
- Test coverage improvements
- Performance optimizations
- Example configurations

**Not suitable**:
- Large refactors without discussion
- Breaking changes without strong justification
- Features specific to your setup only
- Duplicate functionality

## Questions?

If you have questions about development:

1. Check this guide and other documentation
2. Search existing GitHub issues
3. Ask in a new GitHub issue with "Question" label

**Happy coding!** 🚀

