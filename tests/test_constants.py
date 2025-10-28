"""Tests for constants and XDG path handling."""

import os
from pathlib import Path
import importlib

import pytest

from automation_scripts.dictation import constants


def test_xdg_config_home_default(monkeypatch):
    """Test XDG_CONFIG_HOME defaults to ~/.config when not set."""
    # Remove env var to test default
    monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
    
    # Reload constants module to pick up change
    importlib.reload(constants)
    
    expected = Path.home() / '.config'
    assert constants.XDG_CONFIG_HOME == expected


def test_xdg_config_home_custom(mock_xdg_home, monkeypatch):
    """Test custom XDG_CONFIG_HOME is respected."""
    custom_path = mock_xdg_home / "custom_config"
    monkeypatch.setenv('XDG_CONFIG_HOME', str(custom_path))
    
    importlib.reload(constants)
    
    assert constants.XDG_CONFIG_HOME == custom_path


def test_xdg_data_home_default(monkeypatch):
    """Test XDG_DATA_HOME defaults to ~/.local/share when not set."""
    monkeypatch.delenv('XDG_DATA_HOME', raising=False)
    
    importlib.reload(constants)
    
    expected = Path.home() / '.local' / 'share'
    assert constants.XDG_DATA_HOME == expected


def test_xdg_data_home_custom(mock_xdg_home, monkeypatch):
    """Test custom XDG_DATA_HOME is respected."""
    custom_path = mock_xdg_home / "custom_data"
    monkeypatch.setenv('XDG_DATA_HOME', str(custom_path))
    
    importlib.reload(constants)
    
    assert constants.XDG_DATA_HOME == custom_path


def test_xdg_cache_home_default(monkeypatch):
    """Test XDG_CACHE_HOME defaults to ~/.cache when not set."""
    monkeypatch.delenv('XDG_CACHE_HOME', raising=False)
    
    importlib.reload(constants)
    
    expected = Path.home() / '.cache'
    assert constants.XDG_CACHE_HOME == expected


def test_xdg_cache_home_custom(mock_xdg_home, monkeypatch):
    """Test custom XDG_CACHE_HOME is respected."""
    custom_path = mock_xdg_home / "custom_cache"
    monkeypatch.setenv('XDG_CACHE_HOME', str(custom_path))
    
    importlib.reload(constants)
    
    assert constants.XDG_CACHE_HOME == custom_path


def test_config_dir_structure(mock_xdg_home, monkeypatch):
    """Test config directory follows XDG structure."""
    monkeypatch.setenv('XDG_CONFIG_HOME', str(mock_xdg_home / ".config"))
    importlib.reload(constants)
    
    expected = mock_xdg_home / ".config" / "automation-scripts"
    assert constants.CONFIG_DIR == expected


def test_data_dir_structure(mock_xdg_home, monkeypatch):
    """Test data directory follows XDG structure."""
    monkeypatch.setenv('XDG_DATA_HOME', str(mock_xdg_home / ".local" / "share"))
    importlib.reload(constants)
    
    expected = mock_xdg_home / ".local" / "share" / "automation-scripts" / "dictation"
    assert constants.DATA_DIR == expected


def test_cache_dir_structure(mock_xdg_home, monkeypatch):
    """Test cache directory follows XDG structure."""
    monkeypatch.setenv('XDG_CACHE_HOME', str(mock_xdg_home / ".cache"))
    importlib.reload(constants)
    
    expected = mock_xdg_home / ".cache" / "automation-scripts" / "dictation"
    assert constants.CACHE_DIR == expected


def test_config_file_location(mock_xdg_home, monkeypatch):
    """Test config file is in XDG_CONFIG_HOME."""
    monkeypatch.setenv('XDG_CONFIG_HOME', str(mock_xdg_home / ".config"))
    importlib.reload(constants)
    
    expected = mock_xdg_home / ".config" / "automation-scripts" / "dictation.toml"
    assert constants.CONFIG_FILE == expected


def test_model_cache_dir_location(mock_xdg_home, monkeypatch):
    """Test model cache directory location."""
    monkeypatch.setenv('XDG_CACHE_HOME', str(mock_xdg_home / ".cache"))
    importlib.reload(constants)
    
    expected = mock_xdg_home / ".cache" / "automation-scripts" / "dictation" / "models"
    assert constants.MODEL_CACHE_DIR == expected


def test_lock_file_location():
    """Test lock file remains in /tmp for compatibility."""
    # Lock file should always be in /tmp regardless of XDG settings
    assert constants.LOCK_FILE == Path('/tmp/dictation.lock')


def test_temp_dir_location():
    """Test temp directory is in /tmp."""
    assert constants.TEMP_DIR == Path('/tmp/dictation')


def test_ensure_directories_exist(mock_xdg_home, monkeypatch):
    """Test that ensure_directories_exist creates required directories."""
    monkeypatch.setenv('XDG_CONFIG_HOME', str(mock_xdg_home / ".config"))
    monkeypatch.setenv('XDG_DATA_HOME', str(mock_xdg_home / ".local" / "share"))
    monkeypatch.setenv('XDG_CACHE_HOME', str(mock_xdg_home / ".cache"))
    
    importlib.reload(constants)
    
    # Directories should be created
    dirs = constants.ensure_directories_exist()
    
    assert 'config' in dirs
    assert 'data' in dirs
    assert 'cache' in dirs
    assert 'model_cache' in dirs
    assert 'temp' in dirs
    
    # Verify they actually exist
    assert dirs['config'].exists()
    assert dirs['data'].exists()
    assert dirs['cache'].exists()
    assert dirs['model_cache'].exists()
    # temp dir might not be in mock_xdg_home, so we skip existence check


def test_ensure_directories_exist_idempotent(mock_xdg_home, monkeypatch):
    """Test that ensure_directories_exist can be called multiple times safely."""
    monkeypatch.setenv('XDG_CONFIG_HOME', str(mock_xdg_home / ".config"))
    
    importlib.reload(constants)
    
    # Call multiple times should not error
    dirs1 = constants.ensure_directories_exist()
    dirs2 = constants.ensure_directories_exist()
    
    assert dirs1 == dirs2


def test_default_constants_exist():
    """Test that all default constants are defined."""
    # Whisper defaults
    assert hasattr(constants, 'DEFAULT_WHISPER_MODEL')
    assert hasattr(constants, 'DEFAULT_DEVICE')
    assert hasattr(constants, 'DEFAULT_COMPUTE_TYPE')
    assert hasattr(constants, 'DEFAULT_LANGUAGE')
    assert hasattr(constants, 'DEFAULT_BEAM_SIZE')
    assert hasattr(constants, 'DEFAULT_TEMPERATURE')
    
    # Audio defaults
    assert hasattr(constants, 'DEFAULT_AUDIO_DEVICE')
    assert hasattr(constants, 'DEFAULT_SAMPLE_RATE')
    assert hasattr(constants, 'DEFAULT_CHANNELS')
    
    # Text defaults
    assert hasattr(constants, 'DEFAULT_PASTE_METHOD')
    assert hasattr(constants, 'DEFAULT_TYPING_DELAY')
    assert hasattr(constants, 'DEFAULT_AUTO_CAPITALIZE')
    assert hasattr(constants, 'DEFAULT_STRIP_SPACES')
    
    # Notification defaults
    assert hasattr(constants, 'DEFAULT_NOTIFICATIONS_ENABLED')
    assert hasattr(constants, 'DEFAULT_NOTIFICATION_TOOL')
    assert hasattr(constants, 'DEFAULT_NOTIFICATION_URGENCY')
    
    # File defaults
    assert hasattr(constants, 'DEFAULT_KEEP_TEMP_FILES')


def test_default_values_are_sensible():
    """Test that default values have sensible types and values."""
    # Whisper
    assert isinstance(constants.DEFAULT_WHISPER_MODEL, str)
    assert constants.DEFAULT_WHISPER_MODEL in ['tiny.en', 'base.en', 'small.en', 'medium.en', 'large']
    assert constants.DEFAULT_DEVICE in ['cpu', 'cuda', 'auto']
    assert constants.DEFAULT_COMPUTE_TYPE in ['int8', 'int16', 'float16', 'float32']
    assert isinstance(constants.DEFAULT_BEAM_SIZE, int)
    assert 1 <= constants.DEFAULT_BEAM_SIZE <= 10
    
    # Audio
    assert constants.DEFAULT_SAMPLE_RATE == 16000  # Whisper requirement
    assert constants.DEFAULT_CHANNELS == 1  # Whisper requirement
    
    # Text
    assert constants.DEFAULT_PASTE_METHOD in ['xdotool', 'clipboard', 'both']
    assert isinstance(constants.DEFAULT_TYPING_DELAY, int)
    assert constants.DEFAULT_TYPING_DELAY > 0


def test_env_var_mapping_exists():
    """Test that ENV_VAR_MAPPING is defined and valid."""
    assert hasattr(constants, 'ENV_VAR_MAPPING')
    assert isinstance(constants.ENV_VAR_MAPPING, dict)
    assert len(constants.ENV_VAR_MAPPING) > 0


def test_env_var_mapping_structure():
    """Test that ENV_VAR_MAPPING has correct structure."""
    for env_var, mapping in constants.ENV_VAR_MAPPING.items():
        # Each env var should start with prefix
        assert env_var.startswith(constants.ENV_VAR_PREFIX)
        
        # Mapping should be tuple with (section, key)
        assert isinstance(mapping, tuple)
        assert len(mapping) == 2
        assert isinstance(mapping[0], str)  # section
        assert isinstance(mapping[1], str)  # key


def test_env_var_prefix():
    """Test ENV_VAR_PREFIX is defined correctly."""
    assert constants.ENV_VAR_PREFIX == 'DICTATION_'


def test_default_config_dict_exists():
    """Test that DEFAULT_CONFIG dictionary exists."""
    assert hasattr(constants, 'DEFAULT_CONFIG')
    assert isinstance(constants.DEFAULT_CONFIG, dict)


def test_default_config_dict_structure():
    """Test DEFAULT_CONFIG has all required sections."""
    config = constants.DEFAULT_CONFIG
    
    # Required sections
    assert 'whisper' in config
    assert 'audio' in config
    assert 'text' in config
    assert 'notifications' in config
    assert 'files' in config
    
    # Each section should be a dict
    assert isinstance(config['whisper'], dict)
    assert isinstance(config['audio'], dict)
    assert isinstance(config['text'], dict)
    assert isinstance(config['notifications'], dict)
    assert isinstance(config['files'], dict)


def test_default_config_whisper_section():
    """Test DEFAULT_CONFIG whisper section has required keys."""
    whisper = constants.DEFAULT_CONFIG['whisper']
    
    assert 'model' in whisper
    assert 'device' in whisper
    assert 'compute_type' in whisper
    assert 'language' in whisper
    assert 'beam_size' in whisper
    assert 'temperature' in whisper


def test_default_config_audio_section():
    """Test DEFAULT_CONFIG audio section has required keys."""
    audio = constants.DEFAULT_CONFIG['audio']
    
    assert 'device' in audio
    assert 'sample_rate' in audio
    assert 'channels' in audio


def test_default_config_text_section():
    """Test DEFAULT_CONFIG text section has required keys."""
    text = constants.DEFAULT_CONFIG['text']
    
    assert 'paste_method' in text
    assert 'typing_delay' in text
    assert 'auto_capitalize' in text
    assert 'strip_spaces' in text


def test_default_config_notifications_section():
    """Test DEFAULT_CONFIG notifications section has required keys."""
    notifications = constants.DEFAULT_CONFIG['notifications']
    
    assert 'enable' in notifications
    assert 'tool' in notifications
    assert 'urgency' in notifications
    assert 'timeout' in notifications


def test_default_config_files_section():
    """Test DEFAULT_CONFIG files section has required keys."""
    files = constants.DEFAULT_CONFIG['files']
    
    assert 'temp_dir' in files
    assert 'keep_temp_files' in files
    assert 'lock_file' in files


def test_max_recording_duration():
    """Test MAX_RECORDING_DURATION is defined and reasonable."""
    assert hasattr(constants, 'MAX_RECORDING_DURATION')
    assert isinstance(constants.MAX_RECORDING_DURATION, int)
    assert constants.MAX_RECORDING_DURATION > 0


def test_min_recording_duration():
    """Test MIN_RECORDING_DURATION is defined and reasonable."""
    assert hasattr(constants, 'MIN_RECORDING_DURATION')
    assert isinstance(constants.MIN_RECORDING_DURATION, (int, float))
    assert constants.MIN_RECORDING_DURATION > 0
    assert constants.MIN_RECORDING_DURATION < 60  # Should be less than a minute

