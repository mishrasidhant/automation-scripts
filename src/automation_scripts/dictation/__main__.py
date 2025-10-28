"""
CLI entry point for the dictation module.

This module allows running the dictation module as a Python module:
    python -m automation_scripts.dictation --start
    uv run -m automation_scripts.dictation --toggle
"""

from .dictate import main

if __name__ == '__main__':
    main()

