# Story 7: Configuration System Implementation

**Story ID:** DICT-007  
**Epic:** Dictation Module Implementation  
**Priority:** Medium (Quality of Life)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 hours  
**Depends On:** Story 6, Story 6.1  
**Blocks:** None (enhancement)

---

## User Story

**As a** user,  
**I want** to configure the dictation module via the config/dictation.env file,  
**So that** I can customize model, device, and behavior settings without editing Python code.

---

## Problem Statement

The `config/dictation.env` file exists and documents extensive configuration options, but `dictate.py` does not read most of these environment variables. Users must edit Python source code to change settings.

**Current State:**
- ✅ Config file exists with 30+ documented options
- ✅ dictation-toggle.sh sources and exports variables
- ❌ dictate.py only reads `DICTATION_DEBUG` 
- ❌ All other settings are hardcoded (lines 48-63)

**Gap Analysis:**

| Configuration | Documented | Implemented | Gap |
|---------------|-----------|-------------|-----|
| WHISPER_MODEL | ✅ | ❌ | Hardcoded to "base.en" |
| WHISPER_DEVICE | ✅ | ❌ | Hardcoded to "cpu" |
| WHISPER_COMPUTE_TYPE | ✅ | ❌ | Hardcoded to "int8" |
| AUDIO_DEVICE | ✅ | ❌ | Hardcoded to None |
| SAMPLE_RATE | ✅ | ❌ | Hardcoded to 16000 |
| XDOTOOL_DELAY_MS | ✅ | ❌ | Hardcoded to 12 |
| All other settings | ✅ | ❌ | Not read |

**Impact:**
- Users cannot switch Whisper models (speed vs accuracy tradeoff)
- Cannot select specific audio device (multi-mic setups)
- Cannot tune performance settings
- Configuration documentation is misleading

---

## Acceptance Criteria

### Functional Requirements

1. **dictate.py reads all documented environment variables**
   - WHISPER_MODEL - model selection
   - WHISPER_DEVICE - cpu/cuda
   - WHISPER_COMPUTE_TYPE - int8/int16/float16/float32
   - WHISPER_LANGUAGE - language hint
   - WHISPER_BEAM_SIZE - accuracy vs speed
   - WHISPER_TEMPERATURE - determinism
   - WHISPER_VAD_FILTER - voice activity detection
   - WHISPER_INITIAL_PROMPT - context hint

2. **Audio configuration is respected**
   - AUDIO_DEVICE - device selection
   - SAMPLE_RATE - sampling rate
   - CHANNELS - mono/stereo

3. **Text processing settings work**
   - PASTE_METHOD - xdotool/clipboard/both
   - TYPING_DELAY - keystroke delay
   - CLEAR_MODIFIERS - modifier key clearing
   - STRIP_LEADING_SPACE - whitespace trimming
   - STRIP_TRAILING_SPACE - whitespace trimming
   - AUTO_CAPITALIZE - first letter capitalization
   - AUTO_PUNCTUATION - keep whisper punctuation

4. **Notification settings are configurable**
   - ENABLE_NOTIFICATIONS - enable/disable
   - NOTIFICATION_TOOL - notify-send/dunstify
   - NOTIFICATION_URGENCY - low/normal/critical
   - NOTIFICATION_TIMEOUT - milliseconds
   - SHOW_TRANSCRIPTION_IN_NOTIFICATION - show text

5. **File management settings work**
   - TEMP_DIR - temporary file location
   - KEEP_TEMP_FILES - debug mode
   - LOCK_FILE - lock file path
   - LOG_FILE - log file path
   - LOG_LEVEL - DEBUG/INFO/WARNING/ERROR

### Integration Requirements

6. **Backwards compatibility maintained**
   - Script works without config file (uses defaults)
   - Missing env vars fall back to sensible defaults
   - Existing functionality unchanged
   - No breaking changes to CLI interface

7. **Configuration validation**
   - Invalid model names rejected with clear error
   - Invalid device types rejected
   - Invalid file paths handled gracefully
   - Configuration errors reported via notification

### Quality Requirements

8. **Code quality maintained**
   - Configuration loading is centralized
   - Default values clearly defined
   - Type conversion handled safely
   - Configuration documented in code

9. **Testing coverage**
   - Unit tests for config loading
   - Tests for invalid configurations
   - Tests for missing configurations
   - Integration tests with actual config file

---

## Technical Implementation

### Architecture Pattern

**Approach: Environment Variable Loading with Defaults**

```python
# New configuration loading function
def load_config():
    """Load configuration from environment variables with defaults."""
    return {
        'model': os.environ.get('WHISPER_MODEL', 'base.en'),
        'device': os.environ.get('WHISPER_DEVICE', 'cpu'),
        'compute_type': os.environ.get('WHISPER_COMPUTE_TYPE', 'int8'),
        'audio_device': os.environ.get('AUDIO_DEVICE', None),
        'sample_rate': int(os.environ.get('SAMPLE_RATE', '16000')),
        # ... etc
    }
```

### Changes Required

**File:** `modules/dictation/dictate.py`

#### Change 1: Remove Hardcoded Constants (Lines 48-63)

Replace:
```python
# Configuration constants
LOCK_FILE = Path("/tmp/dictation.lock")
TEMP_DIR = Path("/tmp/dictation")
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16

# Transcription configuration
MODEL_NAME = "base.en"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_CACHE = os.path.expanduser("~/.cache/huggingface/hub/")

# Text injection configuration
XDOTOOL_DELAY_MS = 12
DEBUG_MODE = os.environ.get("DICTATION_DEBUG", "").lower() in ("1", "true", "yes")
```

With:
```python
# Configuration loading function
def load_config():
    """Load configuration from environment variables with defaults."""
    config = {
        # Whisper model configuration
        'model': os.environ.get('WHISPER_MODEL', 'base.en'),
        'device': os.environ.get('WHISPER_DEVICE', 'cpu'),
        'compute_type': os.environ.get('WHISPER_COMPUTE_TYPE', 'int8'),
        'language': os.environ.get('WHISPER_LANGUAGE', 'en'),
        'beam_size': int(os.environ.get('WHISPER_BEAM_SIZE', '5')),
        'temperature': float(os.environ.get('WHISPER_TEMPERATURE', '0.0')),
        'vad_filter': os.environ.get('WHISPER_VAD_FILTER', 'true').lower() == 'true',
        'initial_prompt': os.environ.get('WHISPER_INITIAL_PROMPT', ''),
        
        # Audio configuration
        'audio_device': os.environ.get('AUDIO_DEVICE', '') or None,
        'sample_rate': int(os.environ.get('SAMPLE_RATE', '16000')),
        'channels': int(os.environ.get('CHANNELS', '1')),
        
        # Text processing
        'paste_method': os.environ.get('PASTE_METHOD', 'xdotool'),
        'typing_delay': int(os.environ.get('TYPING_DELAY', '12')),
        'clear_modifiers': os.environ.get('CLEAR_MODIFIERS', 'true').lower() == 'true',
        'strip_leading': os.environ.get('STRIP_LEADING_SPACE', 'true').lower() == 'true',
        'strip_trailing': os.environ.get('STRIP_TRAILING_SPACE', 'true').lower() == 'true',
        'auto_capitalize': os.environ.get('AUTO_CAPITALIZE', 'false').lower() == 'true',
        'auto_punctuation': os.environ.get('AUTO_PUNCTUATION', 'true').lower() == 'true',
        
        # Notifications
        'enable_notifications': os.environ.get('ENABLE_NOTIFICATIONS', 'true').lower() == 'true',
        'notification_tool': os.environ.get('NOTIFICATION_TOOL', 'notify-send'),
        'notification_urgency': os.environ.get('NOTIFICATION_URGENCY', 'normal'),
        'notification_timeout': int(os.environ.get('NOTIFICATION_TIMEOUT', '3000')),
        'show_transcription': os.environ.get('SHOW_TRANSCRIPTION_IN_NOTIFICATION', 'true').lower() == 'true',
        
        # File management
        'temp_dir': Path(os.environ.get('TEMP_DIR', '/tmp/dictation')),
        'keep_temp': os.environ.get('KEEP_TEMP_FILES', 'false').lower() == 'true',
        'lock_file': Path(os.environ.get('LOCK_FILE', '/tmp/dictation.lock')),
        'log_file': os.environ.get('LOG_FILE', ''),
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
        
        # Legacy debug mode
        'debug': os.environ.get('DICTATION_DEBUG', '').lower() in ('1', 'true', 'yes'),
    }
    
    # Validation
    valid_models = ['tiny.en', 'base.en', 'small.en', 'medium.en', 'large-v3']
    if config['model'] not in valid_models:
        raise ValueError(f"Invalid model: {config['model']}. Must be one of {valid_models}")
    
    valid_devices = ['cpu', 'cuda']
    if config['device'] not in valid_devices:
        raise ValueError(f"Invalid device: {config['device']}. Must be one of {valid_devices}")
    
    return config

# Load configuration once at module level
try:
    CONFIG = load_config()
except Exception as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    # Fall back to safe defaults
    CONFIG = {
        'model': 'base.en',
        'device': 'cpu',
        'compute_type': 'int8',
        'audio_device': None,
        'sample_rate': 16000,
        # ... minimal defaults
    }
```

#### Change 2: Update All References

Replace hardcoded constants with `CONFIG['key']` throughout:

- `MODEL_NAME` → `CONFIG['model']`
- `DEVICE` → `CONFIG['device']`
- `COMPUTE_TYPE` → `CONFIG['compute_type']`
- `SAMPLE_RATE` → `CONFIG['sample_rate']`
- `XDOTOOL_DELAY_MS` → `CONFIG['typing_delay']`
- etc.

#### Change 3: Update Functions

Functions that use configuration need to access `CONFIG`:

```python
def transcribe_audio(audio_file: Path, model_name: str = None, verbose: bool = False) -> str:
    """Transcribe audio file to text using faster-whisper."""
    
    # Use CONFIG if model_name not specified
    if model_name is None:
        model_name = CONFIG['model']
    
    device = CONFIG['device']
    compute_type = CONFIG['compute_type']
    
    # ... rest of function
```

---

## Implementation Checklist

### Phase 1: Configuration Loading
- [ ] Create `load_config()` function with all settings
- [ ] Add configuration validation
- [ ] Add error handling for invalid configs
- [ ] Test config loading with various env vars
- [ ] Test config loading without env vars (defaults)

### Phase 2: Update dictate.py
- [ ] Replace hardcoded constants with CONFIG dict
- [ ] Update `transcribe_audio()` to use CONFIG
- [ ] Update `record_audio()` to use CONFIG
- [ ] Update `paste_text()` to use CONFIG
- [ ] Update `_send_notification_static()` to use CONFIG
- [ ] Update all other functions using constants

### Phase 3: Text Processing
- [ ] Implement `STRIP_LEADING_SPACE` logic
- [ ] Implement `STRIP_TRAILING_SPACE` logic
- [ ] Implement `AUTO_CAPITALIZE` logic
- [ ] Implement `AUTO_PUNCTUATION` logic
- [ ] Add text processing pipeline

### Phase 4: Testing
- [ ] Add unit tests for `load_config()`
- [ ] Add tests for configuration validation
- [ ] Add tests for invalid configurations
- [ ] Test with config file present
- [ ] Test without config file (defaults)
- [ ] Test with partial config (some vars set)
- [ ] Integration test with actual transcription

### Phase 5: Documentation
- [ ] Update modules/dictation/README.md to remove "Known Limitations"
- [ ] Update CONFIGURATION_OPTIONS.md status
- [ ] Add configuration examples to README
- [ ] Document configuration validation errors

---

## Testing Strategy

### Unit Tests

```python
def test_load_config_defaults():
    """Test config loads with no env vars set."""
    # Clear env
    config = load_config()
    assert config['model'] == 'base.en'
    assert config['device'] == 'cpu'

def test_load_config_custom():
    """Test config loads from env vars."""
    os.environ['WHISPER_MODEL'] = 'tiny.en'
    config = load_config()
    assert config['model'] == 'tiny.en'

def test_load_config_invalid_model():
    """Test invalid model is rejected."""
    os.environ['WHISPER_MODEL'] = 'invalid'
    with pytest.raises(ValueError):
        load_config()
```

### Integration Tests

1. **Test with tiny.en model**
   - Set `WHISPER_MODEL=tiny.en`
   - Transcribe sample audio
   - Verify faster transcription

2. **Test with specific audio device**
   - Set `AUDIO_DEVICE=2`
   - Record audio
   - Verify correct device used

3. **Test with clipboard paste**
   - Set `PASTE_METHOD=clipboard`
   - Transcribe and paste
   - Verify clipboard contains text

---

## Definition of Done

- ✅ `load_config()` function reads all documented env vars
- ✅ All hardcoded constants replaced with CONFIG references
- ✅ Configuration validation rejects invalid values
- ✅ Backwards compatible (works without config file)
- ✅ Unit tests for configuration loading
- ✅ Integration tests with actual config changes
- ✅ Documentation updated to reflect working config
- ✅ "Known Limitations" section removed from README
- ✅ All existing tests still pass
- ✅ Manual testing with different configurations

---

## Dependencies

### No New Dependencies

This story only refactors existing code to read environment variables.

---

## Risk Assessment

### Risks

1. **Breaking existing functionality**
   - **Mitigation:** Comprehensive testing, backwards compatibility
   - **Likelihood:** Medium (extensive refactoring)

2. **Configuration errors causing crashes**
   - **Mitigation:** Validation, error handling, safe defaults
   - **Likelihood:** Low (good error handling)

3. **Performance impact from config loading**
   - **Mitigation:** Load once at module level
   - **Likelihood:** Very Low (one-time operation)

### Rollback Plan

If critical issues found:
1. Git revert to Story 6.1 state
2. Keep hardcoded defaults
3. Add config as future enhancement

---

## Technical Notes

### Configuration Best Practices

1. **Environment variables over config files** - Unix philosophy
2. **Sensible defaults** - Work out of box
3. **Validation early** - Fail fast on bad config
4. **Clear error messages** - Help users fix issues

### Design Decisions

**Why environment variables?**
- Already using shell wrapper (dictation-toggle.sh)
- Follows 12-factor app principles
- Easy to override per-invocation
- No new file formats or parsers needed

**Why load once at module level?**
- Performance: avoid repeated parsing
- Consistency: same config for entire run
- Simplicity: no config passing through functions

---

## Example Usage (After Implementation)

### Scenario 1: Fast Mode for Quick Notes

```bash
# Edit config/dictation.env
WHISPER_MODEL="tiny.en"
WHISPER_BEAM_SIZE=3

# Use dictation
./dictation-toggle.sh
# Now uses tiny.en (2x faster, slightly less accurate)
```

### Scenario 2: High Accuracy for Important Documents

```bash
WHISPER_MODEL="small.en"
WHISPER_BEAM_SIZE=7
./dictation-toggle.sh
```

### Scenario 3: Multi-Microphone Setup

```bash
AUDIO_DEVICE="2"  # Blue Microphones
./dictation-toggle.sh
```

---

## Related Documentation

- **Story 6:** `docs/stories/story-6-documentation-testing.md`
- **Story 6.1:** `docs/stories/story-6.1-fix-test-suite.md`
- **Config Reference:** `docs/CONFIGURATION_OPTIONS.md`
- **Module README:** `modules/dictation/README.md`
- **Config File:** `modules/dictation/config/dictation.env`

---

## Dev Agent Notes

This is a **medium-complexity refactoring story**. The pattern is clear:

1. Create centralized config loading
2. Replace all hardcoded constants
3. Add validation
4. Test thoroughly

The bulk of the work is the careful replacement of constants throughout the codebase.

**Estimated actual time:** 
- Config function: 30 min
- Refactor constants: 60 min
- Text processing: 30 min
- Testing: 30 min
- Total: ~2.5 hours

---

**Story Status:** Ready for Implementation  
**Prerequisites:** Story 6, Story 6.1 complete  
**Blocks:** None (quality enhancement)  
**Next Story:** TBD

---

## Agent Model Used

- orchestrator: Claude Sonnet 4.5
- pm: Claude Sonnet 4.5

## Dev Agent Record

### Tasks
- [ ] Create `load_config()` function with all 30+ configuration options
- [ ] Add configuration validation (model names, device types, file paths)
- [ ] Replace all hardcoded constants (MODEL_NAME, DEVICE, etc.) with CONFIG references
- [ ] Update `transcribe_audio()` to use CONFIG['model'], CONFIG['device'], CONFIG['compute_type']
- [ ] Update `record_audio()` to use CONFIG['audio_device'], CONFIG['sample_rate']
- [ ] Update `paste_text()` to use CONFIG['typing_delay'], CONFIG['paste_method']
- [ ] Implement text processing pipeline (strip spaces, capitalize, punctuation)
- [ ] Update notification functions to use CONFIG settings
- [ ] Add unit tests for config loading
- [ ] Add integration tests with different configurations
- [ ] Update README.md to remove "Known Limitations" section
- [ ] Add configuration examples to documentation

### Debug Log

### Completion Notes

### File List

### Change Log

### Status
Draft

