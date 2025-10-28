# Story Documentation Index

## Current Stories (UV-Based Implementation)

### Epic: UV Migration & Modernization

| Story | Title | Status | Document |
|-------|-------|--------|----------|
| DICT-008 | UV Migration | ✅ Complete | [story-8-uv-migration.md](story-8-uv-migration.md) |
| DICT-009 | Systemd Hotkey Service | ✅ Complete | [story-9-systemd-hotkey.md](story-9-systemd-hotkey.md) |
| DICT-010 | Fix SIGTERM Hang | ✅ Complete | [story-10-fix-sigterm-hang.md](story-10-fix-sigterm-hang.md) |
| DICT-010.5 | Startup Reliability Fix | ✅ Complete | [story-10.5-startup-fix.md](story-10.5-startup-fix.md) |
| DICT-010.6 | Enhanced Diagnostics | ✅ Complete | [story-10.6-enhanced-diagnostics.md](story-10.6-enhanced-diagnostics.md) |
| DICT-011 | Config Test Documentation | ✅ Complete | [story-11-config-test-docs.md](story-11-config-test-docs.md) |
| DICT-012 | Post-UV Cleanup | 🚧 In Progress | [story-12-post-uv-cleanup.md](story-12-post-uv-cleanup.md) |

## Archived Stories (Pre-UV Era - Pip-Based)

> ⚠️ **DEPRECATED:** The stories below describe a pip-based implementation that has been
> replaced by the UV-based approach (Story 8+). They are preserved for historical reference
> and to understand the project's evolution. **Do not follow these stories for current development.**

### Epic: Initial Dictation Module Implementation (Deprecated)

| Story | Title | Status | Document | Notes |
|-------|-------|--------|----------|-------|
| DICT-001 | Audio Recording | 🗄️ Archived | [story-1-audio-recording.md](story-1-audio-recording.md) | Pip-based, flat module structure |
| DICT-002 | Speech Transcription | 🗄️ Archived | [story-2-speech-transcription.md](story-2-speech-transcription.md) | Pip-based |
| DICT-003 | Text Injection | 🗄️ Archived | [story-3-text-injection.md](story-3-text-injection.md) | Pip-based |
| DICT-004 | Hotkey Wrapper | 🗄️ Archived | [story-4-hotkey-wrapper.md](story-4-hotkey-wrapper.md) | .env config (superseded) |
| DICT-005 | Setup Script | 🗄️ Archived | [story-5-setup-script.md](story-5-setup-script.md) | Pip installation (superseded) |
| DICT-006 | Documentation & Testing | 🗄️ Archived | [story-6-documentation-testing.md](story-6-documentation-testing.md) | Pip-based |
| DICT-006.1 | Fix Test Suite | 🗄️ Archived | [story-6.1-fix-test-suite.md](story-6.1-fix-test-suite.md) | Pip-based |
| DICT-007 | Configuration System | 🗄️ Archived | [story-7-configuration-system.md](story-7-configuration-system.md) | .env config (superseded by TOML) |
| DICT-007 | Implementation Plan | 🗄️ Archived | [story-7-implementation-plan.md](story-7-implementation-plan.md) | .env config planning |

**Migration Cutover:** Story 8 (UV Migration) replaced the entire implementation. All code from Stories 1-7 was rewritten or migrated.

**Preserved For:**
- Understanding original design decisions
- Historical context for architecture evolution
- Reference for migration lessons learned
