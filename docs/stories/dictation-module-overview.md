# Dictation Module - Implementation Stories

**Epic:** Voice-to-Text Dictation Module - Complete Implementation  
**Created:** October 26, 2025  
**PM:** John  
**Status:** Ready for Implementation

---

## Epic Goal

Implement a complete voice-to-text dictation system for Manjaro Linux + XFCE that allows the user to transcribe speech to text using a system-wide hotkey (Ctrl+'), leveraging local AI processing (faster-whisper) with no cloud dependencies.

---

## Epic Context

### Existing System Integration

- **Project:** automation-scripts (automation tooling for Linux)
- **Technology Stack:** Python 3.13.7, Bash, systemd, XFCE
- **Target System:** Manjaro Linux, XFCE, X11, PulseAudio
- **Architecture Status:** ✅ Fully designed (see DICTATION_ARCHITECTURE.md)

### What's Being Added

A complete dictation module that enables:
1. System-wide hotkey trigger (Ctrl+')
2. Audio recording from Blue Microphones USB Audio
3. Local speech-to-text transcription using faster-whisper
4. Text injection at cursor position using xdotool
5. Visual feedback via desktop notifications
6. User-configurable settings

### Success Criteria

- User presses Ctrl+' → records audio → presses Ctrl+' again → text appears at cursor
- Transcription latency under 3 seconds for 10 seconds of speech
- Accuracy ≥95% for clear English speech
- No root/sudo required for normal operation
- All processing happens locally (no cloud APIs)

---

## Implementation Stories

This epic is broken down into 6 logically sequenced stories that can be implemented incrementally with validation at each stage.

### Story Sequence

```
Story 1: Core Audio Recording
    ↓
Story 2: Speech Transcription Integration
    ↓
Story 3: Text Injection & State Management
    ↓
Story 4: Hotkey Integration & Configuration
    ↓
Story 5: Automated Setup & Dependency Management
    ↓
Story 6: Documentation & Testing Validation
```

---

## Story Summaries

### 1. Core Dictation Script - Audio Recording
**Focus:** Implement audio capture using sounddevice + PulseAudio  
**Files:** `modules/dictation/dictate.py` (initial version)  
**Deliverable:** Can record audio to WAV file on command

### 2. Speech Transcription Integration
**Focus:** Integrate faster-whisper for speech-to-text  
**Files:** `dictate.py` (add transcription)  
**Deliverable:** Can transcribe WAV file to text

### 3. Text Injection & State Management
**Focus:** Text pasting via xdotool, lock file state management  
**Files:** `dictate.py` (complete core functionality)  
**Deliverable:** Full record → transcribe → paste workflow

### 4. Hotkey Wrapper & Configuration
**Focus:** Toggle script for XFCE hotkey integration  
**Files:** `dictation-toggle.sh`, `config/dictation.env`  
**Deliverable:** Hotkey can trigger dictation workflow

### 5. Automated Setup Script
**Focus:** Dependency validation and automated installation  
**Files:** `setup.sh`  
**Deliverable:** One-command setup for new installations

### 6. Documentation & Testing
**Focus:** User-facing documentation and validation testing  
**Files:** `README.md`, test scripts  
**Deliverable:** Production-ready module with docs

---

## Technical Approach

### Architecture Pattern
**On-Demand Trigger** (not persistent daemon)
```
User Hotkey → XFCE → dictation-toggle.sh → dictate.py → Transcribe → Paste
```

### Key Technologies
- **Audio:** sounddevice + PulseAudio
- **Speech Recognition:** faster-whisper (base.en model)
- **Text Injection:** xdotool (X11)
- **Notifications:** notify-send
- **State Management:** Lock file (`/tmp/dictation.lock`)
- **Hotkey:** XFCE native keyboard shortcuts

### Module Structure
```
modules/dictation/
├── README.md                    # User documentation
├── dictate.py                   # Core recording + transcription
├── dictation-toggle.sh          # Hotkey wrapper script
├── setup.sh                     # Automated setup
└── config/
    └── dictation.env            # User configuration
```

---

## Compatibility & Risk

### Compatibility Requirements
- ✅ No changes to existing automation-scripts functionality
- ✅ Self-contained module (can be enabled/disabled independently)
- ✅ No root/sudo required for normal operation
- ✅ Works with existing system tools (XFCE, PulseAudio, X11)

### Risk Assessment
**Primary Risk:** Audio device conflicts or permission issues  
**Mitigation:** Dependency validation in setup, clear error messages  
**Rollback:** Remove module directory, delete XFCE hotkey binding

### Testing Strategy
- Unit tests for core functions (record, transcribe, paste)
- Integration test: full workflow end-to-end
- Manual validation: different audio lengths, edge cases
- Performance baseline: measure latency on target system

---

## Definition of Done

Epic is complete when:
- ✅ All 6 stories completed with acceptance criteria met
- ✅ User can dictate text using Ctrl+' hotkey
- ✅ Setup script successfully installs dependencies
- ✅ Documentation covers installation and usage
- ✅ Performance meets latency targets (<3s overhead)
- ✅ No regression in existing automation-scripts functionality

---

## Dependencies

### System Dependencies (to be installed)
- xdotool
- portaudio
- libnotify (already installed)

### Python Dependencies (to be installed)
- sounddevice
- faster-whisper
- numpy (already installed)

### External Resources
- faster-whisper model (base.en, ~145MB, auto-downloaded)

---

## Estimated Effort

| Story | Complexity | Estimated Time |
|-------|------------|----------------|
| Story 1 | Medium | 2-3 hours |
| Story 2 | Medium | 2-3 hours |
| Story 3 | High | 3-4 hours |
| Story 4 | Low | 1-2 hours |
| Story 5 | Medium | 2-3 hours |
| Story 6 | Low | 1-2 hours |
| **Total** | | **11-17 hours** |

---

## Reference Documentation

- **Architecture:** `docs/DICTATION_ARCHITECTURE.md`
- **System Profile:** `docs/SYSTEM_PROFILE.md`
- **Configuration:** `docs/CONFIGURATION_OPTIONS.md`
- **Setup Checklist:** `docs/SETUP_CHECKLIST.md`

---

## Next Steps

1. Review and approve these stories
2. Begin with Story 1 (audio recording foundation)
3. Implement incrementally with validation at each stage
4. Test thoroughly on target system
5. Deploy and document for user

---

**Epic Status:** Ready for Implementation  
**Architecture:** Complete  
**Stories:** Defined (6 stories)  
**Ready to Start:** ✅ Yes

