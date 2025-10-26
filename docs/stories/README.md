# Dictation Module - User Stories

This directory contains the complete implementation stories for the dictation module.

## 📋 Story Overview

The dictation module has been broken down into **6 implementation-ready user stories** that can be completed sequentially.

| Story | Title | Complexity | Effort | Status |
|-------|-------|------------|--------|--------|
| [DICT-001](story-1-audio-recording.md) | Core Audio Recording | Medium | 2-3h | ✅ Ready |
| [DICT-002](story-2-speech-transcription.md) | Speech Transcription Integration | Medium | 2-3h | ✅ Ready |
| [DICT-003](story-3-text-injection.md) | Text Injection & State Management | High | 3-4h | ✅ Ready |
| [DICT-004](story-4-hotkey-wrapper.md) | Hotkey Wrapper & Configuration | Low | 1-2h | ✅ Ready |
| [DICT-005](story-5-setup-script.md) | Automated Setup Script | Medium | 2-3h | ✅ Ready |
| [DICT-006](story-6-documentation-testing.md) | Documentation & Testing | Low | 1-2h | ✅ Ready |
| **TOTAL** | | | **11-17h** | |

---

## 🎯 Epic Goal

Implement a complete voice-to-text dictation system for Manjaro Linux + XFCE that allows the user to transcribe speech to text using a system-wide hotkey (Ctrl+'), leveraging local AI processing (faster-whisper) with no cloud dependencies.

---

## 📖 How to Use These Stories

### For Developers

1. **Read the [Epic Overview](dictation-module-overview.md)** first to understand the complete picture
2. **Implement stories sequentially** (each depends on the previous)
3. **Complete all acceptance criteria** before moving to next story
4. **Run tests** at the end of each story to validate
5. **Get PM approval** before proceeding (if following formal process)

### Implementation Sequence

```
Story 1 (Foundation)
  ↓ (audio recording works)
Story 2 (Add AI transcription)
  ↓ (transcription works)
Story 3 (Complete core functionality)
  ↓ (full workflow: record → transcribe → paste)
Story 4 (User interface)
  ↓ (hotkey integration)
Story 5 (Installation automation)
  ↓ (easy setup for end users)
Story 6 (Polish & delivery)
  ↓
✅ Production-Ready Module
```

### Story Structure

Each story contains:
- **User Story:** What and why
- **Acceptance Criteria:** Measurable requirements
- **Implementation Checklist:** Step-by-step tasks
- **Testing Strategy:** How to validate
- **Definition of Done:** Clear completion criteria
- **Technical Details:** Code examples and guidance

---

## 📂 Deliverables

Upon completion of all stories, the module will have:

```
modules/dictation/
├── README.md                    # User documentation
├── dictate.py                   # Core recording + transcription script
├── dictation-toggle.sh          # Hotkey wrapper script
├── setup.sh                     # Automated installation
├── test-dictation.sh            # Validation test suite
└── config/
    └── dictation.env            # User configuration
```

---

## 🏗️ Architecture Reference

These stories implement the architecture defined in:
- [`docs/DICTATION_ARCHITECTURE.md`](../DICTATION_ARCHITECTURE.md) - Complete technical design
- [`docs/SYSTEM_PROFILE.md`](../SYSTEM_PROFILE.md) - Target system details
- [`docs/CONFIGURATION_OPTIONS.md`](../CONFIGURATION_OPTIONS.md) - Configuration guide
- [`docs/ARCHITECTURE_SUMMARY.md`](../ARCHITECTURE_SUMMARY.md) - Key decisions

---

## 🔧 Technical Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Hotkey Manager** | XFCE Native Shortcuts | Zero overhead, built-in |
| **Speech Recognition** | faster-whisper | 4x faster than OpenAI |
| **Audio Capture** | sounddevice + PulseAudio | Python-native, reliable |
| **Text Injection** | xdotool | Standard for X11 |
| **Notifications** | notify-send | XFCE integration |
| **State Management** | Lock file | Simple IPC |

---

## ✅ Success Criteria

The implementation is successful when:

1. ✅ User presses Ctrl+' → records audio → presses Ctrl+' again → text appears at cursor
2. ✅ Transcription latency under 3 seconds for 10 seconds of speech
3. ✅ Accuracy ≥95% for clear English speech
4. ✅ No root/sudo required for normal operation
5. ✅ All processing happens locally (no cloud APIs)
6. ✅ Setup is automated and takes <5 minutes
7. ✅ Documentation is complete and clear
8. ✅ All tests pass

---

## 📊 Estimated Timeline

| Phase | Duration | Stories |
|-------|----------|---------|
| **Foundation** | 4-6 hours | Story 1-2 |
| **Core Functionality** | 3-4 hours | Story 3 |
| **User Interface** | 1-2 hours | Story 4 |
| **Polish & Delivery** | 3-5 hours | Story 5-6 |
| **TOTAL** | **11-17 hours** | All 6 stories |

*Note: Estimates are for focused development time and do not include breaks, testing, or debugging.*

---

## 🚀 Quick Start Guide (For After Implementation)

Once all stories are complete:

```bash
# 1. Install
cd modules/dictation
./setup.sh

# 2. Use
Press Ctrl+'         # Start recording
(speak your text)
Press Ctrl+' again   # Stop and paste

# 3. Configure
nano config/dictation.env

# 4. Test
./test-dictation.sh
```

---

## 📝 Story Details

### Story 1: Core Audio Recording
**Focus:** Implement foundation - audio capture using sounddevice  
**Deliverable:** Can record audio to WAV file via CLI arguments  
**Prerequisites:** None (foundation story)  
**Read more:** [story-1-audio-recording.md](story-1-audio-recording.md)

### Story 2: Speech Transcription Integration
**Focus:** Integrate faster-whisper for speech-to-text  
**Deliverable:** Can transcribe WAV files to text  
**Prerequisites:** Story 1 complete  
**Read more:** [story-2-speech-transcription.md](story-2-speech-transcription.md)

### Story 3: Text Injection & State Management
**Focus:** Complete core workflow with text pasting and toggle mode  
**Deliverable:** Full record → transcribe → paste workflow  
**Prerequisites:** Story 1 + Story 2 complete  
**Read more:** [story-3-text-injection.md](story-3-text-injection.md)

### Story 4: Hotkey Wrapper & Configuration
**Focus:** Create wrapper script for hotkey integration  
**Deliverable:** Hotkey can trigger dictation workflow  
**Prerequisites:** Story 3 complete (toggle mode)  
**Read more:** [story-4-hotkey-wrapper.md](story-4-hotkey-wrapper.md)

### Story 5: Automated Setup Script
**Focus:** Dependency validation and automated installation  
**Deliverable:** One-command setup for new installations  
**Prerequisites:** Story 4 complete (all files exist)  
**Read more:** [story-5-setup-script.md](story-5-setup-script.md)

### Story 6: Documentation & Testing
**Focus:** User-facing documentation and validation testing  
**Deliverable:** Production-ready module with complete docs  
**Prerequisites:** Story 5 complete (entire module functional)  
**Read more:** [story-6-documentation-testing.md](story-6-documentation-testing.md)

---

## 🎓 Learning Path

If you're new to this codebase:

1. **Start with Epic Overview** - Understand the big picture
2. **Read Architecture docs** - Understand the design decisions
3. **Review Story 1** - Understand the foundation
4. **Implement incrementally** - Build and validate as you go
5. **Run tests frequently** - Catch issues early
6. **Document as you build** - Keep README updated

---

## 🤝 Contributing

When implementing these stories:

1. **Follow the architecture** documented in DICTATION_ARCHITECTURE.md
2. **Meet all acceptance criteria** listed in each story
3. **Test thoroughly** using manual and automated tests
4. **Update documentation** as you implement features
5. **Keep it simple** - follow existing patterns in the codebase

---

## 📞 Support

For questions or issues:

- **Architecture questions:** See `docs/DICTATION_ARCHITECTURE.md`
- **Configuration help:** See `docs/CONFIGURATION_OPTIONS.md`
- **Setup issues:** See `docs/SETUP_CHECKLIST.md`
- **Story clarification:** Review individual story files

---

## ✨ Key Features (When Complete)

- 🎤 **System-wide hotkey** - Works in any application
- 🤖 **Local AI processing** - No cloud, complete privacy
- ⚡ **Fast transcription** - ~4x realtime with base.en model
- 🎯 **High accuracy** - 95%+ for clear English speech
- 🔧 **Fully configurable** - Customize models, hotkeys, behavior
- 🚀 **Easy setup** - Automated installation and configuration
- 📚 **Well documented** - Complete user and technical docs

---

**Version:** 1.0  
**Created:** October 26, 2025  
**Status:** All stories ready for implementation  
**PM:** John

---

## Next Steps

1. Review the [Epic Overview](dictation-module-overview.md)
2. Start with [Story 1: Audio Recording](story-1-audio-recording.md)
3. Implement sequentially through Story 6
4. Deliver production-ready module! 🚀

