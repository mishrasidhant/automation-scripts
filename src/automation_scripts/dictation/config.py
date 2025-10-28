"""
Configuration management for the dictation module.

This module handles loading configuration from multiple sources with proper
precedence: CLI arguments > Environment variables > TOML file > Defaults

Uses Python 3.11+ built-in tomllib for TOML parsing.
"""

import os
import sys
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import (
    CONFIG_FILE,
    DEFAULT_CONFIG,
    ENV_VAR_MAPPING,
    ENV_VAR_PREFIX,
)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration with precedence: ENV > TOML > Defaults.
    
    Configuration loading order (highest to lowest precedence):
    1. Environment variables (DICTATION_*)
    2. TOML configuration file (~/.config/automation-scripts/dictation.toml)
    3. Hardcoded defaults (from constants.py)
    
    Args:
        config_path: Optional path to TOML config file. If None, uses default location.
    
    Returns:
        Dictionary containing merged configuration from all sources
    
    Raises:
        ConfigurationError: If TOML file exists but is invalid
    """
    # Start with defaults
    config = deepcopy(DEFAULT_CONFIG)
    
    # Load and merge TOML configuration if it exists
    toml_config = load_toml_config(config_path)
    if toml_config:
        config = merge_config(config, toml_config)
    
    # Apply environment variable overrides
    config = apply_env_overrides(config)
    
    # Validate the final configuration
    validate_config(config)
    
    return config


def load_toml_config(config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load TOML configuration file if it exists.
    
    Args:
        config_path: Path to TOML file. If None, uses CONFIG_FILE from constants.
    
    Returns:
        Dictionary with TOML configuration, or None if file doesn't exist
    
    Raises:
        ConfigurationError: If TOML file exists but cannot be parsed
    """
    path = config_path or CONFIG_FILE
    
    if not path.exists():
        return None
    
    try:
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigurationError(
            f"Invalid TOML configuration file at {path}: {e}"
        )
    except Exception as e:
        raise ConfigurationError(
            f"Error reading configuration file at {path}: {e}"
        )


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Environment variables follow the pattern: DICTATION_SECTION_KEY
    Examples:
        DICTATION_WHISPER_MODEL=tiny.en
        DICTATION_AUDIO_DEVICE=hw:0
        DICTATION_TYPING_DELAY=20
    
    Args:
        config: Base configuration dictionary
    
    Returns:
        Configuration with environment variable overrides applied
    """
    config = deepcopy(config)
    
    for env_var, (section, key) in ENV_VAR_MAPPING.items():
        value = os.environ.get(env_var)
        if value is not None:
            # Type conversion based on default value type
            if section in config and key in config[section]:
                default_value = config[section][key]
                converted_value = convert_value(value, type(default_value))
                config[section][key] = converted_value
            else:
                # New key from environment variable
                if section not in config:
                    config[section] = {}
                config[section][key] = value
    
    return config


def convert_value(value: str, target_type: type) -> Any:
    """
    Convert string value to target type.
    
    Args:
        value: String value from environment variable
        target_type: Target type to convert to
    
    Returns:
        Converted value
    
    Raises:
        ConfigurationError: If conversion fails
    """
    try:
        if target_type == bool:
            # Handle boolean conversion specially
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        else:
            return value
    except (ValueError, AttributeError) as e:
        raise ConfigurationError(
            f"Cannot convert '{value}' to {target_type.__name__}: {e}"
        )


def merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary
    
    Returns:
        Merged configuration with overrides applied
    """
    result = deepcopy(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_config(result[key], value)
        else:
            # Override value
            result[key] = value
    
    return result


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary to validate
    
    Raises:
        ConfigurationError: If any configuration value is invalid
    """
    errors = []
    
    # Validate Whisper model
    valid_models = [
        'tiny', 'tiny.en',
        'base', 'base.en',
        'small', 'small.en',
        'medium', 'medium.en',
        'large', 'large-v1', 'large-v2', 'large-v3',
        'large-v3-turbo',
    ]
    model = config.get('whisper', {}).get('model', '')
    if model and model not in valid_models:
        errors.append(
            f"Invalid Whisper model '{model}'. "
            f"Valid options: {', '.join(valid_models)}"
        )
    
    # Validate device
    valid_devices = ['cpu', 'cuda', 'auto']
    device = config.get('whisper', {}).get('device', '')
    if device and device not in valid_devices:
        errors.append(
            f"Invalid device '{device}'. "
            f"Valid options: {', '.join(valid_devices)}"
        )
    
    # Validate compute type
    valid_compute_types = ['int8', 'int16', 'float16', 'float32']
    compute_type = config.get('whisper', {}).get('compute_type', '')
    if compute_type and compute_type not in valid_compute_types:
        errors.append(
            f"Invalid compute_type '{compute_type}'. "
            f"Valid options: {', '.join(valid_compute_types)}"
        )
    
    # Validate beam size
    beam_size = config.get('whisper', {}).get('beam_size')
    if beam_size is not None and (beam_size < 1 or beam_size > 10):
        errors.append(
            f"Invalid beam_size {beam_size}. Must be between 1 and 10."
        )
    
    # Validate sample rate
    sample_rate = config.get('audio', {}).get('sample_rate')
    if sample_rate is not None and sample_rate != 16000:
        errors.append(
            f"Invalid sample_rate {sample_rate}. "
            f"Whisper requires 16000 Hz."
        )
    
    # Validate channels
    channels = config.get('audio', {}).get('channels')
    if channels is not None and channels != 1:
        errors.append(
            f"Invalid channels {channels}. Whisper requires mono (1 channel)."
        )
    
    # Validate paste method
    valid_paste_methods = ['xdotool', 'clipboard', 'both']
    paste_method = config.get('text', {}).get('paste_method', '')
    if paste_method and paste_method not in valid_paste_methods:
        errors.append(
            f"Invalid paste_method '{paste_method}'. "
            f"Valid options: {', '.join(valid_paste_methods)}"
        )
    
    # Validate typing delay
    typing_delay = config.get('text', {}).get('typing_delay')
    if typing_delay is not None and (typing_delay < 0 or typing_delay > 1000):
        errors.append(
            f"Invalid typing_delay {typing_delay}. Must be between 0 and 1000 ms."
        )
    
    # Validate notification urgency
    valid_urgencies = ['low', 'normal', 'critical']
    urgency = config.get('notifications', {}).get('urgency', '')
    if urgency and urgency not in valid_urgencies:
        errors.append(
            f"Invalid notification urgency '{urgency}'. "
            f"Valid options: {', '.join(valid_urgencies)}"
        )
    
    if errors:
        raise ConfigurationError(
            "Configuration validation failed:\n" +
            "\n".join(f"  - {error}" for error in errors)
        )


def get_config_value(config: Dict[str, Any], section: str, key: str, default: Any = None) -> Any:
    """
    Safely get a configuration value with fallback.
    
    Args:
        config: Configuration dictionary
        section: Configuration section name
        key: Configuration key name
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    return config.get(section, {}).get(key, default)


def print_config(config: Dict[str, Any]) -> None:
    """
    Print configuration in a human-readable format.
    
    Args:
        config: Configuration dictionary to print
    """
    print("Current Configuration:")
    print("=" * 60)
    
    for section, values in sorted(config.items()):
        print(f"\n[{section}]")
        if isinstance(values, dict):
            for key, value in sorted(values.items()):
                print(f"  {key} = {value}")
        else:
            print(f"  {values}")
    
    print("\n" + "=" * 60)


def get_config_sources() -> Dict[str, str]:
    """
    Get information about configuration sources.
    
    Returns:
        Dictionary with paths and status of configuration sources
    """
    return {
        'toml_file': str(CONFIG_FILE),
        'toml_exists': CONFIG_FILE.exists(),
        'env_prefix': ENV_VAR_PREFIX,
        'env_vars_set': [
            var for var in ENV_VAR_MAPPING.keys()
            if os.environ.get(var) is not None
        ],
    }


# Convenience function for CLI
def main():
    """Print current configuration for debugging."""
    try:
        config = load_config()
        print_config(config)
        
        print("\nConfiguration Sources:")
        sources = get_config_sources()
        print(f"  TOML file: {sources['toml_file']}")
        print(f"  TOML exists: {sources['toml_exists']}")
        print(f"  Environment prefix: {sources['env_prefix']}")
        if sources['env_vars_set']:
            print(f"  Environment variables set:")
            for var in sources['env_vars_set']:
                print(f"    - {var} = {os.environ.get(var)}")
        else:
            print(f"  Environment variables set: None")
        
        return 0
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

