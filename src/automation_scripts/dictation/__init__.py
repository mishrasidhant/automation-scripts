"""
Voice dictation module for automation-scripts.

Provides local voice-to-text functionality using faster-whisper AI,
with audio recording, transcription, and text injection capabilities.

Usage:
    from automation_scripts.dictation import main
    main()

Or via command line:
    uv run dictation-toggle --start
    uv run dictation-toggle --stop
    uv run dictation-toggle --toggle
"""

from .dictate import main

__all__ = ["main"]

