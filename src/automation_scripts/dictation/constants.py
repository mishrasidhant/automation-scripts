"""
Constants and XDG-compliant path definitions for the dictation module.

This module defines all configuration paths following the XDG Base Directory
specification, along with default settings for the dictation functionality.

XDG Specification: https://specifications.freedesktop.org/basedir-spec/latest/
"""

import os
from pathlib import Path

# =============================================================================
# XDG Base Directory Specification
# =============================================================================

# XDG base directories with fallback defaults
XDG_CONFIG_HOME = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
XDG_DATA_HOME = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
XDG_CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))

# Application-specific directories
CONFIG_DIR = XDG_CONFIG_HOME / 'automation-scripts'
DATA_DIR = XDG_DATA_HOME / 'automation-scripts' / 'dictation'
CACHE_DIR = XDG_CACHE_HOME / 'automation-scripts' / 'dictation'

# Configuration file paths
CONFIG_FILE = CONFIG_DIR / 'dictation.toml'

# Runtime files (kept in /tmp for compatibility)
LOCK_FILE = Path('/tmp/dictation.lock')
TEMP_DIR = Path('/tmp/dictation')

# =============================================================================
# Whisper Model Configuration Defaults
# =============================================================================

# Available models: tiny.en, base.en, small.en, medium.en, large-v1, large-v2, large-v3
DEFAULT_WHISPER_MODEL = 'base.en'

# Device selection: 'cpu', 'cuda', 'auto'
DEFAULT_DEVICE = 'cpu'

# Compute type affects speed/accuracy tradeoff
# Options: 'int8', 'int16', 'float16', 'float32'
# int8: Fastest, lower accuracy (good for CPU)
# float16: Better accuracy (good for GPU)
# float32: Best accuracy, slowest
DEFAULT_COMPUTE_TYPE = 'int8'

# Language code (ISO 639-1)
DEFAULT_LANGUAGE = 'en'

# Beam size for transcription (1-10)
# Higher = more accurate but slower
DEFAULT_BEAM_SIZE = 5

# Temperature for sampling (0.0 = deterministic)
DEFAULT_TEMPERATURE = 0.0

# VAD (Voice Activity Detection) filter
# Helps remove silence/background noise
DEFAULT_VAD_FILTER = True

# =============================================================================
# Audio Configuration Defaults
# =============================================================================

# Audio device name or 'default' for system default
DEFAULT_AUDIO_DEVICE = 'default'

# Sample rate in Hz (Whisper requires 16kHz)
DEFAULT_SAMPLE_RATE = 16000

# Number of audio channels (Whisper requires mono)
DEFAULT_CHANNELS = 1

# Audio format for temporary files
DEFAULT_AUDIO_FORMAT = 'wav'

# =============================================================================
# Text Injection Configuration Defaults
# =============================================================================

# Text injection method: 'xdotool', 'clipboard', 'both'
DEFAULT_PASTE_METHOD = 'xdotool'

# Delay in milliseconds between keystrokes when typing
# Lower = faster typing, but may cause issues
# Higher = slower but more reliable
DEFAULT_TYPING_DELAY = 12

# Post-processing options
DEFAULT_AUTO_CAPITALIZE = False
DEFAULT_STRIP_SPACES = True
DEFAULT_ADD_PERIOD = False

# =============================================================================
# Notification Configuration Defaults
# =============================================================================

# Enable desktop notifications
DEFAULT_NOTIFICATIONS_ENABLED = True

# Notification tool: 'notify-send' or 'dunstify'
DEFAULT_NOTIFICATION_TOOL = 'notify-send'

# Notification urgency: 'low', 'normal', 'critical'
DEFAULT_NOTIFICATION_URGENCY = 'normal'

# Notification timeout in milliseconds (0 = default, -1 = never expire)
DEFAULT_NOTIFICATION_TIMEOUT = 3000

# Notification icon (can be path to image or icon name)
DEFAULT_NOTIFICATION_ICON = 'microphone'

# =============================================================================
# File Management Configuration Defaults
# =============================================================================

# Keep temporary audio files for debugging
DEFAULT_KEEP_TEMP_FILES = False

# Maximum age of temp files before cleanup (in days)
DEFAULT_TEMP_FILE_MAX_AGE = 7

# Model cache directory (Whisper models downloaded here)
MODEL_CACHE_DIR = CACHE_DIR / 'models'

# =============================================================================
# Runtime Configuration
# =============================================================================

# Maximum recording duration in seconds (safety limit)
MAX_RECORDING_DURATION = 300  # 5 minutes

# Minimum recording duration in seconds (ignore very short recordings)
MIN_RECORDING_DURATION = 0.5

# =============================================================================
# Directory Creation Helper
# =============================================================================

def ensure_directories_exist():
    """
    Create all required XDG directories if they don't exist.
    
    This function is called during module initialization to ensure
    all necessary directories are present with correct permissions.
    
    Returns:
        dict: Dictionary mapping directory names to Path objects
    """
    directories = {
        'config': CONFIG_DIR,
        'data': DATA_DIR,
        'cache': CACHE_DIR,
        'model_cache': MODEL_CACHE_DIR,
        'temp': TEMP_DIR,
    }
    
    for name, path in directories.items():
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Ensure user-only permissions for config directory
            if name == 'config':
                path.chmod(0o700)
        except Exception as e:
            # Log error but don't fail - let the calling code handle it
            print(f"Warning: Could not create {name} directory at {path}: {e}")
    
    return directories


# Create directories on module import
_DIRECTORIES = ensure_directories_exist()

# =============================================================================
# Environment Variable Mapping
# =============================================================================

# Map environment variables to configuration keys
# Used by config.py for environment variable overrides
ENV_VAR_PREFIX = 'DICTATION_'

ENV_VAR_MAPPING = {
    # Whisper configuration
    f'{ENV_VAR_PREFIX}WHISPER_MODEL': ('whisper', 'model'),
    f'{ENV_VAR_PREFIX}DEVICE': ('whisper', 'device'),
    f'{ENV_VAR_PREFIX}COMPUTE_TYPE': ('whisper', 'compute_type'),
    f'{ENV_VAR_PREFIX}LANGUAGE': ('whisper', 'language'),
    f'{ENV_VAR_PREFIX}BEAM_SIZE': ('whisper', 'beam_size'),
    f'{ENV_VAR_PREFIX}TEMPERATURE': ('whisper', 'temperature'),
    f'{ENV_VAR_PREFIX}VAD_FILTER': ('whisper', 'vad_filter'),
    
    # Audio configuration
    f'{ENV_VAR_PREFIX}AUDIO_DEVICE': ('audio', 'device'),
    f'{ENV_VAR_PREFIX}SAMPLE_RATE': ('audio', 'sample_rate'),
    
    # Text injection
    f'{ENV_VAR_PREFIX}PASTE_METHOD': ('text', 'paste_method'),
    f'{ENV_VAR_PREFIX}TYPING_DELAY': ('text', 'typing_delay'),
    f'{ENV_VAR_PREFIX}AUTO_CAPITALIZE': ('text', 'auto_capitalize'),
    
    # Notifications
    f'{ENV_VAR_PREFIX}NOTIFICATIONS_ENABLED': ('notifications', 'enable'),
    f'{ENV_VAR_PREFIX}NOTIFICATION_TOOL': ('notifications', 'tool'),
    f'{ENV_VAR_PREFIX}NOTIFICATION_URGENCY': ('notifications', 'urgency'),
    
    # Files
    f'{ENV_VAR_PREFIX}TEMP_DIR': ('files', 'temp_dir'),
    f'{ENV_VAR_PREFIX}KEEP_TEMP_FILES': ('files', 'keep_temp_files'),
}

# =============================================================================
# Default Configuration Dictionary
# =============================================================================

DEFAULT_CONFIG = {
    'whisper': {
        'model': DEFAULT_WHISPER_MODEL,
        'device': DEFAULT_DEVICE,
        'compute_type': DEFAULT_COMPUTE_TYPE,
        'language': DEFAULT_LANGUAGE,
        'beam_size': DEFAULT_BEAM_SIZE,
        'temperature': DEFAULT_TEMPERATURE,
        'vad_filter': DEFAULT_VAD_FILTER,
    },
    'audio': {
        'device': DEFAULT_AUDIO_DEVICE,
        'sample_rate': DEFAULT_SAMPLE_RATE,
        'channels': DEFAULT_CHANNELS,
    },
    'text': {
        'paste_method': DEFAULT_PASTE_METHOD,
        'typing_delay': DEFAULT_TYPING_DELAY,
        'auto_capitalize': DEFAULT_AUTO_CAPITALIZE,
        'strip_spaces': DEFAULT_STRIP_SPACES,
        'add_period': DEFAULT_ADD_PERIOD,
    },
    'notifications': {
        'enable': DEFAULT_NOTIFICATIONS_ENABLED,
        'tool': DEFAULT_NOTIFICATION_TOOL,
        'urgency': DEFAULT_NOTIFICATION_URGENCY,
        'timeout': DEFAULT_NOTIFICATION_TIMEOUT,
        'icon': DEFAULT_NOTIFICATION_ICON,
    },
    'files': {
        'temp_dir': str(TEMP_DIR),
        'keep_temp_files': DEFAULT_KEEP_TEMP_FILES,
        'lock_file': str(LOCK_FILE),
    },
}

