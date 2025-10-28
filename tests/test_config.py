"""Tests for configuration loading and validation."""

import os
from pathlib import Path

import pytest

from automation_scripts.dictation import config
from automation_scripts.dictation.config import ConfigurationError


def test_load_config_with_missing_file_uses_defaults(mock_xdg_home, monkeypatch, clean_env):
    """Test that missing config file loads defaults without error."""
    # Ensure config file doesn't exist
    config_file = mock_xdg_home / ".config" / "automation-scripts" / "dictation.toml"
    assert not config_file.exists()
    
    # Mock the CONFIG_FILE to point to non-existent location
    monkeypatch.setattr(config, 'CONFIG_FILE', config_file)
    
    # Should load defaults successfully
    cfg = config.load_config()
    assert cfg is not None
    assert 'whisper' in cfg
    assert cfg['whisper']['model'] == 'base.en'  # Default model


def test_load_config_from_toml_file(mock_xdg_home, monkeypatch, clean_env):
    """Test loading configuration from TOML file."""
    # Create config file
    config_path = mock_xdg_home / ".config" / "automation-scripts"
    config_path.mkdir(parents=True, exist_ok=True)
    config_file = config_path / "dictation.toml"
    config_file.write_text('''
[whisper]
model = "small.en"
beam_size = 10

[text]
typing_delay = 20
''')
    
    # Mock CONFIG_FILE to use our test file
    monkeypatch.setattr(config, 'CONFIG_FILE', config_file)
    
    cfg = config.load_config()
    assert cfg['whisper']['model'] == 'small.en'
    assert cfg['whisper']['beam_size'] == 10
    assert cfg['text']['typing_delay'] == 20


def test_load_config_with_invalid_toml_raises_error(tmp_config_file, monkeypatch, clean_env):
    """Test that invalid TOML syntax raises ConfigurationError."""
    # Create file with invalid TOML
    config_file = tmp_config_file('this is not valid toml [[[')
    monkeypatch.setattr(config, 'CONFIG_FILE', config_file)
    
    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        config.load_config()


def test_env_override_whisper_model(sample_config, env_override, clean_env):
    """Test environment variable override for Whisper model."""
    env_override('DICTATION_WHISPER_MODEL', 'tiny.en')
    
    cfg = config.apply_env_overrides(sample_config.copy())
    assert cfg['whisper']['model'] == 'tiny.en'


def test_env_override_multiple_values(sample_config, env_override, clean_env):
    """Test multiple environment variable overrides."""
    env_override('DICTATION_WHISPER_MODEL', 'small.en')
    env_override('DICTATION_AUDIO_DEVICE', 'hw:1')
    env_override('DICTATION_TYPING_DELAY', '25')
    
    cfg = config.apply_env_overrides(sample_config.copy())
    assert cfg['whisper']['model'] == 'small.en'
    assert cfg['audio']['device'] == 'hw:1'
    assert cfg['text']['typing_delay'] == 25


def test_env_override_boolean_values(sample_config, env_override, clean_env):
    """Test boolean environment variable parsing."""
    test_cases = [
        ('true', True),
        ('True', True),
        ('1', True),
        ('yes', True),
        ('false', False),
        ('False', False),
        ('0', False),
        ('no', False),
    ]
    
    for raw_value, expected in test_cases:
        cfg = sample_config.copy()
        env_override('DICTATION_NOTIFICATIONS_ENABLED', raw_value)
        cfg = config.apply_env_overrides(cfg)
        assert cfg['notifications']['enable'] == expected, f"Failed for {raw_value}"


def test_env_override_integer_values(sample_config, env_override, clean_env):
    """Test integer environment variable parsing."""
    env_override('DICTATION_BEAM_SIZE', '8')
    env_override('DICTATION_TYPING_DELAY', '15')
    
    cfg = config.apply_env_overrides(sample_config.copy())
    assert cfg['whisper']['beam_size'] == 8
    assert isinstance(cfg['whisper']['beam_size'], int)
    assert cfg['text']['typing_delay'] == 15
    assert isinstance(cfg['text']['typing_delay'], int)


def test_env_override_float_values(sample_config, env_override, clean_env):
    """Test float environment variable parsing."""
    env_override('DICTATION_TEMPERATURE', '0.5')
    
    cfg = config.apply_env_overrides(sample_config.copy())
    assert cfg['whisper']['temperature'] == 0.5
    assert isinstance(cfg['whisper']['temperature'], float)


def test_validate_config_valid(sample_config):
    """Test validation passes for valid config."""
    # Should not raise any exception
    config.validate_config(sample_config)


def test_validate_config_invalid_model(sample_config):
    """Test validation catches invalid Whisper model."""
    sample_config['whisper']['model'] = 'invalid-model'
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'invalid-model' in str(exc_info.value).lower()
    assert 'whisper model' in str(exc_info.value).lower()


def test_validate_config_invalid_device(sample_config):
    """Test validation catches invalid device."""
    sample_config['whisper']['device'] = 'invalid-device'
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'invalid-device' in str(exc_info.value).lower()
    assert 'device' in str(exc_info.value).lower()


def test_validate_config_invalid_compute_type(sample_config):
    """Test validation catches invalid compute type."""
    sample_config['whisper']['compute_type'] = 'invalid-compute'
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'compute_type' in str(exc_info.value).lower()


def test_validate_config_beam_size_out_of_range(sample_config):
    """Test validation catches beam size out of range."""
    sample_config['whisper']['beam_size'] = 500  # Too high
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'beam_size' in str(exc_info.value).lower()
    
    # Test lower bound
    sample_config['whisper']['beam_size'] = 0  # Too low
    with pytest.raises(ConfigurationError):
        config.validate_config(sample_config)


def test_validate_config_invalid_sample_rate(sample_config):
    """Test validation catches invalid sample rate."""
    sample_config['audio']['sample_rate'] = 44100  # Wrong rate
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'sample_rate' in str(exc_info.value).lower()
    assert '16000' in str(exc_info.value)


def test_validate_config_invalid_channels(sample_config):
    """Test validation catches invalid channel count."""
    sample_config['audio']['channels'] = 2  # Stereo not supported
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'channels' in str(exc_info.value).lower()
    assert 'mono' in str(exc_info.value).lower()


def test_validate_config_typing_delay_out_of_range(sample_config):
    """Test validation catches typing delay out of range."""
    sample_config['text']['typing_delay'] = 5000  # Too high
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'typing_delay' in str(exc_info.value).lower()


def test_validate_config_invalid_paste_method(sample_config):
    """Test validation catches invalid paste method."""
    sample_config['text']['paste_method'] = 'invalid-method'
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'paste_method' in str(exc_info.value).lower()


def test_validate_config_invalid_urgency(sample_config):
    """Test validation catches invalid notification urgency."""
    sample_config['notifications']['urgency'] = 'super-urgent'
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate_config(sample_config)
    
    assert 'urgency' in str(exc_info.value).lower()


def test_merge_config_simple():
    """Test merging two configuration dictionaries."""
    base = {'whisper': {'model': 'base.en', 'device': 'cpu'}}
    override = {'whisper': {'model': 'tiny.en'}}
    
    result = config.merge_config(base, override)
    
    assert result['whisper']['model'] == 'tiny.en'  # Overridden
    assert result['whisper']['device'] == 'cpu'     # Preserved


def test_merge_config_nested():
    """Test merging nested configuration sections."""
    base = {
        'whisper': {'model': 'base.en'},
        'audio': {'device': 'default'},
    }
    override = {
        'whisper': {'beam_size': 10},
        'text': {'typing_delay': 20},
    }
    
    result = config.merge_config(base, override)
    
    assert result['whisper']['model'] == 'base.en'     # Preserved
    assert result['whisper']['beam_size'] == 10        # Added
    assert result['audio']['device'] == 'default'      # Preserved
    assert result['text']['typing_delay'] == 20        # Added


def test_convert_value_bool():
    """Test boolean value conversion."""
    assert config.convert_value('true', bool) is True
    assert config.convert_value('false', bool) is False
    assert config.convert_value('1', bool) is True
    assert config.convert_value('0', bool) is False


def test_convert_value_int():
    """Test integer value conversion."""
    assert config.convert_value('42', int) == 42
    assert config.convert_value('-10', int) == -10


def test_convert_value_float():
    """Test float value conversion."""
    assert config.convert_value('3.14', float) == 3.14
    assert config.convert_value('0.5', float) == 0.5


def test_convert_value_str():
    """Test string value conversion (passthrough)."""
    assert config.convert_value('hello', str) == 'hello'


def test_convert_value_invalid_raises_error():
    """Test that invalid conversion raises ConfigurationError."""
    with pytest.raises(ConfigurationError):
        config.convert_value('not-a-number', int)
    
    with pytest.raises(ConfigurationError):
        config.convert_value('not-a-float', float)


def test_get_config_value():
    """Test safe config value retrieval."""
    cfg = {'whisper': {'model': 'base.en'}}
    
    assert config.get_config_value(cfg, 'whisper', 'model') == 'base.en'
    assert config.get_config_value(cfg, 'whisper', 'missing', 'default') == 'default'
    assert config.get_config_value(cfg, 'missing_section', 'key', 'default') == 'default'


def test_get_config_sources():
    """Test retrieval of config source information."""
    sources = config.get_config_sources()
    
    assert 'toml_file' in sources
    assert 'toml_exists' in sources
    assert 'env_prefix' in sources
    assert 'env_vars_set' in sources
    assert sources['env_prefix'] == 'DICTATION_'


def test_full_config_load_precedence(tmp_config_file, monkeypatch, env_override, clean_env):
    """Test complete configuration loading with precedence: ENV > TOML > Defaults."""
    # Create TOML file with specific values
    config_file = tmp_config_file('''
[whisper]
model = "small.en"
beam_size = 8

[text]
typing_delay = 15
''')
    monkeypatch.setattr(config, 'CONFIG_FILE', config_file)
    
    # Set environment variable to override TOML
    env_override('DICTATION_WHISPER_MODEL', 'tiny.en')
    
    # Load config
    cfg = config.load_config()
    
    # Environment variable takes precedence
    assert cfg['whisper']['model'] == 'tiny.en'
    
    # TOML values used where no env override
    assert cfg['whisper']['beam_size'] == 8
    assert cfg['text']['typing_delay'] == 15
    
    # Defaults used where neither TOML nor env set
    assert cfg['whisper']['compute_type'] == 'int8'


def test_load_config_creates_complete_structure(clean_env, monkeypatch, mock_xdg_home):
    """Test that load_config returns all expected sections."""
    config_file = mock_xdg_home / ".config" / "automation-scripts" / "dictation.toml"
    monkeypatch.setattr(config, 'CONFIG_FILE', config_file)
    
    cfg = config.load_config()
    
    # Check all required sections exist
    assert 'whisper' in cfg
    assert 'audio' in cfg
    assert 'text' in cfg
    assert 'notifications' in cfg
    assert 'files' in cfg

