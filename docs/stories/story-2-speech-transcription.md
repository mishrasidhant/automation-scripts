# Story 2: Speech Transcription Integration

**Story ID:** DICT-002  
**Epic:** Dictation Module Implementation  
**Priority:** High (Core Functionality)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 hours  
**Depends On:** Story 1 (Audio Recording)

---

## User Story

**As a** user who has recorded audio,  
**I want** the system to transcribe my speech to text using local AI,  
**So that** I can convert my voice into written text without cloud dependencies.

---

## Story Context

### Existing System Integration

- **Builds on:** Story 1 (dictate.py with audio recording)
- **Technology:** faster-whisper library, Python 3.13.7
- **AI Model:** base.en (145MB, auto-downloaded)
- **Processing:** Local CPU inference (no GPU required)

### Technical Approach

Extend `dictate.py` to:
- Load faster-whisper model on demand
- Transcribe WAV files created by Story 1
- Return transcribed text as output
- Handle model loading/caching efficiently
- Provide user feedback during transcription

---

## Acceptance Criteria

### Functional Requirements

1. **Script accepts transcription command**
   - `python3 dictate.py --transcribe <audio_file>` transcribes audio
   - Returns transcribed text to stdout
   - Non-zero exit code on error

2. **Whisper model loads and caches efficiently**
   - Model downloads automatically on first run
   - Cached model reused on subsequent runs
   - Model location: `~/.cache/huggingface/hub/`
   - Uses base.en model by default

3. **Transcription produces accurate English text**
   - Accuracy ≥95% for clear speech
   - Handles natural pauses and sentence boundaries
   - Includes punctuation from Whisper
   - Strips leading/trailing whitespace

### Integration Requirements

4. **Works with audio files from Story 1**
   - Accepts WAV files at 16kHz sample rate
   - Handles variable audio lengths (1s to 5 minutes)
   - Processes mono audio correctly

5. **Model configuration is flexible**
   - Model name can be specified (tiny.en, base.en, small.en)
   - Compute type configurable (int8, float16, float32)
   - Device configurable (cpu, cuda)
   - Defaults optimized for user's CPU system

6. **Transcription progress is visible to user**
   - Desktop notification shows "Transcribing..." when started
   - Desktop notification shows result when complete
   - Console output includes timing information (debug mode)

### Quality Requirements

7. **Performance meets target latency**
   - Transcription speed: ~4x realtime (10s audio in ~2.5s)
   - First-run model load: acceptable 1-2s delay
   - Subsequent runs: model already loaded in memory

8. **Error handling for transcription issues**
   - Invalid audio file: clear error message
   - Model download failure: helpful guidance
   - Insufficient memory: graceful degradation message
   - Empty/silent audio: return empty string gracefully

9. **Resource usage is reasonable**
   - Memory: ~600MB for base.en model
   - CPU: Uses available cores efficiently
   - No memory leaks on repeated transcriptions

---

## Technical Implementation Details

### Extended File Structure

```
modules/dictation/
├── dictate.py          # Extended with transcription (this story)
└── config/             # (Still empty, Story 4 will populate)
```

### Key Python Components

```python
# Additional imports for this story
from faster_whisper import WhisperModel
import time
import logging

# Model configuration
MODEL_NAME = "base.en"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_CACHE = os.path.expanduser("~/.cache/huggingface/hub/")
```

### Transcription Function Signature

```python
def transcribe_audio(audio_file: str, model_name: str = "base.en") -> str:
    """
    Transcribe audio file to text using faster-whisper.
    
    Args:
        audio_file: Path to WAV file (16kHz, mono)
        model_name: Whisper model to use (tiny.en, base.en, small.en)
    
    Returns:
        Transcribed text as string
    
    Raises:
        FileNotFoundError: If audio file doesn't exist
        RuntimeError: If transcription fails
    """
    pass
```

### CLI Argument Extension

```python
parser.add_argument('--transcribe', type=str, metavar='FILE',
                    help='Transcribe audio file to text')
parser.add_argument('--model', type=str, default='base.en',
                    choices=['tiny.en', 'base.en', 'small.en', 'medium.en'],
                    help='Whisper model to use (default: base.en)')
```

---

## Implementation Checklist

### Phase 1: Model Integration
- [ ] Install faster-whisper library
- [ ] Import WhisperModel class
- [ ] Implement model loading function
- [ ] Test model download on first run
- [ ] Verify model caching works

### Phase 2: Transcription Function
- [ ] Implement `transcribe_audio()` function
- [ ] Load audio file and validate format
- [ ] Call WhisperModel.transcribe()
- [ ] Process segments into single text string
- [ ] Strip whitespace and normalize output

### Phase 3: CLI Integration
- [ ] Add `--transcribe` argument to parser
- [ ] Add `--model` argument for model selection
- [ ] Wire up transcribe argument to function
- [ ] Print transcribed text to stdout
- [ ] Add timing information in verbose mode

### Phase 4: User Feedback
- [ ] Show "Transcribing..." notification on start
- [ ] Show transcribed text in completion notification
- [ ] Add progress indicator (if model supports)
- [ ] Include transcription time in output

### Phase 5: Error Handling & Optimization
- [ ] Handle missing audio file gracefully
- [ ] Handle model download failures
- [ ] Handle empty/silent audio
- [ ] Add retry logic for transient failures
- [ ] Optimize model loading (lazy load)

---

## Testing Strategy

### Unit Tests

```python
# Test transcription accuracy
def test_transcribe_known_audio():
    # Use pre-recorded audio with known text
    # Verify transcription matches expected
    pass

# Test model loading
def test_model_loads_successfully():
    # First run: download and load
    # Second run: load from cache
    pass

# Test error handling
def test_invalid_audio_file():
    # Pass non-existent file
    # Verify error message, non-zero exit
    pass
```

### Manual Tests

1. **Basic Transcription Test**
   ```bash
   # Record audio from Story 1
   python3 dictate.py --start
   # Say: "This is a test of the dictation system."
   python3 dictate.py --stop
   
   # Transcribe
   python3 dictate.py --transcribe /tmp/dictation/recording-*.wav
   # Expected output: "This is a test of the dictation system."
   ```

2. **Model Selection Test**
   ```bash
   # Try tiny.en model (faster, less accurate)
   python3 dictate.py --transcribe audio.wav --model tiny.en
   
   # Try base.en model (balanced)
   python3 dictate.py --transcribe audio.wav --model base.en
   
   # Compare accuracy and speed
   ```

3. **Long Audio Test**
   ```bash
   # Record 30-60 seconds of speech
   # Transcribe and verify no memory issues
   # Measure transcription time
   ```

4. **Silent Audio Test**
   ```bash
   # Create silent WAV file
   # Transcribe and verify graceful handling
   ```

5. **First-Run Model Download Test**
   ```bash
   # Clear model cache
   rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-base.en
   
   # Run transcription (should download model)
   python3 dictate.py --transcribe audio.wav
   
   # Verify model downloads to correct location
   ls -lh ~/.cache/huggingface/hub/
   ```

---

## Definition of Done

- ✅ Script can transcribe WAV files using `--transcribe` argument
- ✅ faster-whisper model downloads automatically on first run
- ✅ Transcription accuracy ≥95% for clear English speech
- ✅ Transcription speed meets 4x realtime target (base.en on CPU)
- ✅ Desktop notifications show transcription progress
- ✅ Error handling covers invalid files and model issues
- ✅ Multiple model options available (tiny.en, base.en, small.en)
- ✅ Manual tests pass with good accuracy
- ✅ Memory usage stays within expected bounds (~600MB)

---

## Dependencies

### Python Dependencies
- faster-whisper (needs installation: `pip install faster-whisper`)
- numpy (already installed ✓)
- sounddevice (already installed from Story 1 ✓)

### System Dependencies
- No additional system dependencies for this story
- Uses existing CPU (no GPU required)

### Model Dependencies
- base.en model (~145MB, auto-downloaded)
- Model stored in: `~/.cache/huggingface/hub/`
- Requires ~500MB disk space for model cache

### Installation Commands
```bash
# Install faster-whisper
pip install faster-whisper

# First run will download model automatically
python3 dictate.py --transcribe test.wav
```

---

## Example Usage (After Implementation)

```bash
# Scenario 1: Basic transcription
$ python3 dictate.py --transcribe /tmp/dictation/recording-12345.wav
This is a test of the dictation system.

# Scenario 2: Using different model
$ python3 dictate.py --transcribe audio.wav --model tiny.en
faster transcription with slightly lower accuracy

# Scenario 3: Full workflow (record + transcribe)
$ python3 dictate.py --start
🎙️ Recording started...

# (speak for 10 seconds)

$ python3 dictate.py --stop
✅ Recording stopped. Saved to: /tmp/dictation/recording-12345.wav

$ python3 dictate.py --transcribe /tmp/dictation/recording-12345.wav
⏳ Transcribing...
The quick brown fox jumped over the lazy dog.
✅ Transcription complete (2.3 seconds)
```

---

## Performance Benchmarks (Expected)

Based on target system (Manjaro, CPU inference):

| Audio Length | base.en Time | tiny.en Time | Accuracy (base.en) |
|--------------|--------------|--------------|-------------------|
| 5 seconds    | ~1.2s        | ~0.6s        | 95%+              |
| 10 seconds   | ~2.5s        | ~1.2s        | 95%+              |
| 30 seconds   | ~7.5s        | ~3.8s        | 96%+              |
| 60 seconds   | ~15s         | ~7.5s        | 96%+              |

**Memory Usage:**
- tiny.en: ~400MB
- base.en: ~600MB
- small.en: ~1.2GB

---

## Success Metrics

- **Functionality:** Can transcribe audio to text accurately
- **Accuracy:** ≥95% word accuracy for clear English speech
- **Performance:** Meets 4x realtime speed target
- **Reliability:** No crashes on 20 consecutive transcriptions
- **User Experience:** Clear feedback during transcription process

---

## Technical Notes

### Model Selection Guidance

**For user's system (CPU-only):**

- **tiny.en:** Use if speed is critical, acceptable 85-90% accuracy
- **base.en:** ✅ Recommended - Best balance of speed and accuracy
- **small.en:** Use if accuracy is critical, willing to wait 2x longer

**We default to base.en** as specified in the architecture documentation.

### Whisper Parameters

```python
# Optimized for CPU performance
model = WhisperModel(
    model_size_or_path="base.en",
    device="cpu",
    compute_type="int8",      # Faster on CPU than float32
    cpu_threads=0,            # Use all available cores
    num_workers=1             # Single worker for transcription
)

# Transcription parameters
segments, info = model.transcribe(
    audio_file,
    language="en",            # English only for .en models
    beam_size=5,              # Default, good balance
    vad_filter=True,          # Remove silence
    vad_parameters=dict(      # VAD settings
        min_silence_duration_ms=500
    )
)
```

### Text Processing

```python
# Join segments into single string
text = " ".join(segment.text for segment in segments)

# Post-processing
text = text.strip()           # Remove leading/trailing whitespace
text = " ".join(text.split()) # Normalize internal whitespace

return text
```

---

## Risk Assessment

### Risks

1. **Model download fails (network issue)**
   - **Mitigation:** Retry logic, manual download instructions
   - **Likelihood:** Low

2. **Transcription accuracy below target**
   - **Mitigation:** Allow model switching, test with clear speech
   - **Likelihood:** Low (base.en is proven)

3. **Memory exhaustion on long audio**
   - **Mitigation:** Test with 5-minute audio, warn if too long
   - **Likelihood:** Very Low

4. **CPU overload during transcription**
   - **Mitigation:** This is expected behavior, temporary
   - **Likelihood:** N/A (not a problem)

### Rollback Plan

If transcription fails:
1. Switch to tiny.en model (faster, less memory)
2. Process audio in smaller chunks
3. Fall back to manual transcription (worst case)

---

## Future Integration Points

This story provides:
- **For Story 3:** Transcribed text to be pasted
- **For Story 4:** Model configuration from env file
- **For Story 6:** Transcription accuracy benchmarks

---

## Related Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md` (Whisper engine selection)
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md` (Model settings)
- **Setup Checklist:** `docs/SETUP_CHECKLIST.md` (Whisper validation)

---

**Story Status:** Ready for Implementation  
**Prerequisites:** Story 1 complete (audio recording)  
**Blocks:** Story 3 (text injection)  
**Review Required:** PM approval before starting Story 3

