# Testing Guide

This document describes how to run tests for the automation-scripts project, with a focus on the dictation module.

## Quick Start

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov
```

## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test File

```bash
uv run pytest tests/test_config.py
uv run pytest tests/test_constants.py
```

### Run Specific Test

```bash
uv run pytest tests/test_config.py::test_load_config_with_missing_file_uses_defaults
```

### Run Tests Matching Pattern

```bash
# Run all tests with "config" in the name
uv run pytest -k config

# Run all tests with "env" or "environment" in the name
uv run pytest -k "env or environment"
```

### Run with Verbose Output

```bash
uv run pytest -v
```

### Run with Extra Verbose Output (shows all test names)

```bash
uv run pytest -vv
```

## Coverage Reports

### Generate Coverage Report

```bash
uv run pytest --cov
```

### Generate HTML Coverage Report

```bash
uv run pytest --cov --cov-report=html
```

Then open `htmlcov/index.html` in your browser:

```bash
xdg-open htmlcov/index.html
```

### Coverage for Specific Module

```bash
uv run pytest --cov=automation_scripts.dictation.config
uv run pytest --cov=automation_scripts.dictation.constants
```

### Show Missing Lines

```bash
uv run pytest --cov --cov-report=term-missing
```

## Test Organization

### Test Files

- **`tests/conftest.py`**: Shared pytest fixtures and test configuration
- **`tests/test_config.py`**: Configuration loading and validation tests
- **`tests/test_constants.py`**: XDG path handling and constants tests
- **`modules/dictation/test_dictate.py`**: Existing tests for core dictation module (54 tests)

### Test Categories

#### Unit Tests (Fast, No Hardware Dependencies)

These tests run quickly and don't require any special hardware or system setup:

- Configuration loading
- Configuration validation
- Environment variable overrides
- XDG path creation
- Default value checks

Run only unit tests:

```bash
uv run pytest -m "not integration"
```

#### Integration Tests (Require System Dependencies)

These tests require actual system resources and may not work in all environments:

- Audio device detection (requires PortAudio)
- Audio recording (requires microphone)
- Text injection (requires X11 + xdotool)
- Desktop notifications (requires notify-send/dunstify)

Run only integration tests:

```bash
uv run pytest -m integration
```

**Note:** Integration tests are marked with `@pytest.mark.integration` decorator.

## Test Markers

### Available Markers

- **`unit`**: Fast unit tests with no external dependencies
- **`integration`**: Tests that require hardware or system dependencies
- **`slow`**: Tests that take more than 1 second to run

### Mark a Test

```python
import pytest

@pytest.mark.integration
def test_audio_device_detection():
    # This test requires audio hardware
    devices = list_audio_devices()
    assert len(devices) > 0

@pytest.mark.slow
def test_large_audio_file_transcription():
    # This test takes several seconds
    result = transcribe_audio("long_recording.wav")
    assert result
```

### Run Tests by Marker

```bash
# Skip integration tests
uv run pytest -m "not integration"

# Run only unit tests
uv run pytest -m unit

# Skip slow tests
uv run pytest -m "not slow"
```

## CI/CD Considerations

### Safe Tests for CI (No Hardware Required)

```bash
# Run all tests except integration tests
uv run pytest -m "not integration"
```

These tests are safe to run in CI environments like GitHub Actions, GitLab CI, etc.

### Tests Requiring Hardware (Manual Testing Only)

The following tests require actual hardware and should only be run manually:

- Audio recording tests (need microphone)
- Text injection tests (need X11 display + xdotool)
- Notification tests (need D-Bus session)

These tests should be marked with `@pytest.mark.integration` and skipped in CI.

### Example CI Configuration

**GitHub Actions:**

```yaml
- name: Run tests
  run: |
    uv run pytest -m "not integration" --cov
```

**GitLab CI:**

```yaml
test:
  script:
    - uv run pytest -m "not integration" --cov
```

## Fixtures

### Available Fixtures

#### `tmp_config_file`

Factory fixture to create temporary TOML config files.

```python
def test_something(tmp_config_file):
    config_path = tmp_config_file('''
        [whisper]
        model = "tiny.en"
    ''')
    # Use config_path in test
```

#### `mock_xdg_home`

Mock XDG base directories to use temporary paths.

```python
def test_something(mock_xdg_home):
    # XDG directories now point to temporary paths
    # Clean up happens automatically after test
```

#### `sample_config`

Returns a complete, valid configuration dict.

```python
def test_something(sample_config):
    # Modify as needed for test
    sample_config['whisper']['model'] = 'tiny.en'
```

#### `env_override`

Set environment variables for the test.

```python
def test_something(env_override):
    env_override('DICTATION_WHISPER_MODEL', 'small.en')
    env_override('DICTATION_TYPING_DELAY', '20')
```

#### `clean_env`

Remove all `DICTATION_*` environment variables before test.

```python
def test_something(clean_env):
    # No DICTATION_* env vars are set
```

## Writing New Tests

### Test Naming Convention

- **File**: `test_<module>.py`
- **Function**: `test_<what_it_tests>`
- **Example**: `test_load_config_with_missing_file_uses_defaults`

### Test Structure: Arrange-Act-Assert

```python
def test_validate_config_invalid_model(sample_config):
    # Arrange: Set up test data
    sample_config['whisper']['model'] = 'invalid-model'
    
    # Act: Perform the action
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(sample_config)
    
    # Assert: Check the results
    assert 'invalid-model' in str(exc_info.value).lower()
```

### Use Descriptive Test Names

Good:
```python
def test_load_config_with_missing_file_uses_defaults():
    """Test that missing config file loads defaults without error."""
```

Bad:
```python
def test_config():
    """Test config."""
```

### One Assertion Per Test (Preferably)

Good:
```python
def test_env_override_whisper_model(sample_config, env_override):
    env_override('DICTATION_WHISPER_MODEL', 'tiny.en')
    cfg = apply_env_overrides(sample_config.copy())
    assert cfg['whisper']['model'] == 'tiny.en'

def test_env_override_audio_device(sample_config, env_override):
    env_override('DICTATION_AUDIO_DEVICE', 'hw:1')
    cfg = apply_env_overrides(sample_config.copy())
    assert cfg['audio']['device'] == 'hw:1'
```

### Parameterized Tests

For testing multiple similar cases:

```python
@pytest.mark.parametrize("raw_value,expected", [
    ('true', True),
    ('True', True),
    ('1', True),
    ('false', False),
    ('0', False),
])
def test_bool_conversion(raw_value, expected):
    result = convert_value(raw_value, bool)
    assert result == expected
```

## Debugging Tests

### Show Print Statements

```bash
uv run pytest -s
```

### Drop into Debugger on Failure

```bash
uv run pytest --pdb
```

### Drop into Debugger on First Failure

```bash
uv run pytest -x --pdb
```

### Show Local Variables on Failure

```bash
uv run pytest -l
```

### Run Last Failed Tests Only

```bash
uv run pytest --lf
```

### Run Failed Tests First, Then Others

```bash
uv run pytest --ff
```

## Coverage Goals

### Current Coverage Targets

- **Overall target:** >70% coverage for new modules
- **Focus areas:**
  - `automation_scripts.dictation.config` (configuration loading)
  - `automation_scripts.dictation.constants` (XDG paths and defaults)

### Check Current Coverage

```bash
uv run pytest --cov --cov-report=term-missing
```

### Generate Detailed Coverage Report

```bash
uv run pytest --cov --cov-report=html
xdg-open htmlcov/index.html
```

## Performance

### Fast Execution

The test suite is designed to run quickly:

- **Unit tests:** < 1 second total
- **Full suite (without integration):** < 5 seconds
- **Full suite (with integration):** Variable, depends on hardware

### Slow Tests

If a test takes more than 1 second, mark it as slow:

```python
@pytest.mark.slow
def test_large_model_download():
    # This test downloads a large file
    pass
```

Run without slow tests:

```bash
uv run pytest -m "not slow"
```

## Troubleshooting

### Import Errors

If you see import errors:

```bash
# Ensure package is installed in editable mode
cd /path/to/automation-scripts
uv sync --extra dictation
```

### Module Not Found

Make sure you're in the project root:

```bash
cd /path/to/automation-scripts
uv run pytest
```

### Fixture Not Found

Check that `conftest.py` is in the `tests/` directory and properly formatted.

### Test Failures Due to Environment

Some tests may fail if run with non-standard XDG paths. Use `clean_env` and `mock_xdg_home` fixtures to isolate tests.

## Best Practices

### ✅ Do

- Write descriptive test names
- Use fixtures to avoid code duplication
- Test edge cases and error conditions
- Keep tests fast and isolated
- Mock external dependencies (hardware, network)
- Use `clean_env` to avoid environment pollution

### ❌ Don't

- Write tests that depend on other tests
- Write tests that require manual setup
- Write tests that modify global state
- Write flaky tests (inconsistent results)
- Skip tests without a good reason
- Test implementation details (test behavior, not internals)

## Example Test Session

```bash
$ cd /path/to/automation-scripts

$ uv run pytest -v
========================= test session starts ==========================
collected 45 items

tests/test_config.py::test_load_config_with_missing_file_uses_defaults PASSED
tests/test_config.py::test_load_config_from_toml_file PASSED
tests/test_config.py::test_env_override_whisper_model PASSED
tests/test_config.py::test_validate_config_invalid_model PASSED
...

tests/test_constants.py::test_xdg_config_home_default PASSED
tests/test_constants.py::test_config_dir_structure PASSED
tests/test_constants.py::test_default_constants_exist PASSED
...

========================= 45 passed in 2.34s ===========================
```

## Getting Help

If you encounter issues with tests:

1. Check this README for common solutions
2. Review the test code and fixtures in `conftest.py`
3. Run with verbose output: `uv run pytest -vv`
4. Check the project's main documentation in `docs/`

For questions or bug reports:
- File an issue on the project repository
- Include test output and your environment details
- Mention which tests are failing and any error messages

