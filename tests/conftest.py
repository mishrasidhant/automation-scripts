"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Callable, Iterator

import pytest


@pytest.fixture
def tmp_config_file(tmp_path: Path) -> Callable[[str], Path]:
    """
    Factory fixture to create temporary TOML config files.
    
    Usage:
        def test_something(tmp_config_file):
            config_path = tmp_config_file('''
                [whisper]
                model = "tiny.en"
            ''')
            # Use config_path in test
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
    
    Returns:
        Factory function that creates config files with given content
    """
    def _create_config(content: str) -> Path:
        config_file = tmp_path / "dictation.toml"
        config_file.write_text(content)
        return config_file
    return _create_config


@pytest.fixture
def mock_xdg_home(tmp_path: Path, monkeypatch) -> Path:
    """
    Mock XDG base directories to use temporary paths.
    
    This prevents tests from touching the user's actual config/data directories.
    
    Usage:
        def test_something(mock_xdg_home):
            # XDG directories now point to temporary paths
            # Clean up happens automatically after test
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        monkeypatch: pytest's built-in monkeypatch fixture
    
    Returns:
        Path to temporary home directory
    """
    xdg_config = tmp_path / ".config"
    xdg_data = tmp_path / ".local" / "share"
    xdg_cache = tmp_path / ".cache"
    
    xdg_config.mkdir(parents=True)
    xdg_data.mkdir(parents=True)
    xdg_cache.mkdir(parents=True)
    
    monkeypatch.setenv('XDG_CONFIG_HOME', str(xdg_config))
    monkeypatch.setenv('XDG_DATA_HOME', str(xdg_data))
    monkeypatch.setenv('XDG_CACHE_HOME', str(xdg_cache))
    
    return tmp_path


@pytest.fixture
def sample_config() -> dict:
    """
    Sample valid configuration dict for testing.
    
    Returns a complete, valid configuration that passes validation.
    
    Usage:
        def test_something(sample_config):
            # Modify as needed for test
            sample_config['whisper']['model'] = 'tiny.en'
    
    Returns:
        Dictionary with valid configuration values
    """
    return {
        'whisper': {
            'model': 'base.en',
            'device': 'cpu',
            'compute_type': 'int8',
            'language': 'en',
            'beam_size': 5,
            'temperature': 0.0,
            'vad_filter': True,
        },
        'audio': {
            'device': 'default',
            'sample_rate': 16000,
            'channels': 1,
        },
        'text': {
            'paste_method': 'xdotool',
            'typing_delay': 12,
            'auto_capitalize': False,
            'strip_spaces': True,
            'add_period': False,
        },
        'notifications': {
            'enable': True,
            'tool': 'notify-send',
            'urgency': 'normal',
            'timeout': 3000,
            'icon': 'microphone',
        },
        'files': {
            'temp_dir': '/tmp/dictation',
            'keep_temp_files': False,
            'lock_file': '/tmp/dictation.lock',
        },
    }


@pytest.fixture
def env_override(monkeypatch) -> Callable[[str, str], None]:
    """
    Fixture for setting environment variable overrides.
    
    Usage:
        def test_something(env_override):
            env_override('DICTATION_WHISPER_MODEL', 'small.en')
            env_override('DICTATION_TYPING_DELAY', '20')
            # Environment variables are set for the test
            # Automatically cleaned up after test
    
    Args:
        monkeypatch: pytest's built-in monkeypatch fixture
    
    Returns:
        Function to set environment variables
    """
    def _set_env(key: str, value: str) -> None:
        monkeypatch.setenv(key, value)
    return _set_env


@pytest.fixture
def clean_env(monkeypatch) -> None:
    """
    Clean all DICTATION_* environment variables before test.
    
    Ensures tests start with a clean environment state.
    
    Usage:
        def test_something(clean_env):
            # No DICTATION_* env vars are set
    """
    # Remove any existing DICTATION_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith('DICTATION_'):
            monkeypatch.delenv(key, raising=False)

