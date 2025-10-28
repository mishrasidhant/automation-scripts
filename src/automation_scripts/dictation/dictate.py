#!/usr/bin/env python3
"""
Core dictation script for audio recording and transcription.

This script provides audio recording and speech-to-text transcription capabilities
for the dictation system. It uses sounddevice for audio capture, faster-whisper
for transcription, and manages recording state via lock files.

Usage:
    uv run dictation-toggle --start       # Begin recording
    uv run dictation-toggle --stop        # Stop recording
    uv run dictation-toggle --toggle      # Toggle: start if idle, stop+paste if recording
    uv run dictation-toggle --transcribe <audio_file>  # Transcribe audio
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
import wave
from pathlib import Path

# Import configuration and constants from package modules
from .config import load_config as load_config_new, ConfigurationError
from .constants import (
    LOCK_FILE as CONST_LOCK_FILE,
    TEMP_DIR as CONST_TEMP_DIR,
    MODEL_CACHE_DIR,
)

# Check for required dependencies
try:
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required dependency: {e}", file=sys.stderr)
    print("\nPlease install required packages:", file=sys.stderr)
    print("  uv sync --extra dictation", file=sys.stderr)
    print("\nSystem dependencies (Arch/Manjaro):", file=sys.stderr)
    print("  sudo pacman -S portaudio", file=sys.stderr)
    sys.exit(1)

# Import faster-whisper for transcription (optional for recording-only usage)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


# Load configuration from new config system
try:
    RAW_CONFIG = load_config_new()
except ConfigurationError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Unexpected configuration error: {e}", file=sys.stderr)
    sys.exit(1)

# Convert new config format to old format for backwards compatibility
# This allows the rest of the code to work unchanged
CONFIG = {
    # Whisper model configuration
    'model': RAW_CONFIG.get('whisper', {}).get('model', 'base.en'),
    'device': RAW_CONFIG.get('whisper', {}).get('device', 'cpu'),
    'compute_type': RAW_CONFIG.get('whisper', {}).get('compute_type', 'int8'),
    'language': RAW_CONFIG.get('whisper', {}).get('language', 'en'),
    'beam_size': RAW_CONFIG.get('whisper', {}).get('beam_size', 5),
    'temperature': RAW_CONFIG.get('whisper', {}).get('temperature', 0.0),
    'vad_filter': RAW_CONFIG.get('whisper', {}).get('vad_filter', True),
    'initial_prompt': os.environ.get('DICTATION_WHISPER_INITIAL_PROMPT', ''),
    
    # Audio configuration
    'audio_device': RAW_CONFIG.get('audio', {}).get('device', '') or None,
    'sample_rate': RAW_CONFIG.get('audio', {}).get('sample_rate', 16000),
    'channels': RAW_CONFIG.get('audio', {}).get('channels', 1),
    
    # Text processing
    'paste_method': RAW_CONFIG.get('text', {}).get('paste_method', 'xdotool'),
    'typing_delay': RAW_CONFIG.get('text', {}).get('typing_delay', 12),
    'clear_modifiers': os.environ.get('DICTATION_CLEAR_MODIFIERS', 'true').lower() == 'true',
    'strip_leading': RAW_CONFIG.get('text', {}).get('strip_spaces', True),
    'strip_trailing': RAW_CONFIG.get('text', {}).get('strip_spaces', True),
    'auto_capitalize': RAW_CONFIG.get('text', {}).get('auto_capitalize', False),
    'auto_punctuation': os.environ.get('DICTATION_AUTO_PUNCTUATION', 'true').lower() == 'true',
    'text_replacements': os.environ.get('DICTATION_TEXT_REPLACEMENTS', ''),
    
    # Notifications
    'enable_notifications': RAW_CONFIG.get('notifications', {}).get('enable', True),
    'notification_tool': RAW_CONFIG.get('notifications', {}).get('tool', 'notify-send'),
    'notification_urgency': RAW_CONFIG.get('notifications', {}).get('urgency', 'normal'),
    'notification_timeout': RAW_CONFIG.get('notifications', {}).get('timeout', 3000),
    'show_transcription': os.environ.get('DICTATION_SHOW_TRANSCRIPTION_IN_NOTIFICATION', 'true').lower() == 'true',
    
    # File management
    'temp_dir': Path(RAW_CONFIG.get('files', {}).get('temp_dir', str(CONST_TEMP_DIR))),
    'keep_temp': RAW_CONFIG.get('files', {}).get('keep_temp_files', False),
    'lock_file': Path(RAW_CONFIG.get('files', {}).get('lock_file', str(CONST_LOCK_FILE))),
    'log_file': os.environ.get('DICTATION_LOG_FILE', ''),
    'log_level': os.environ.get('DICTATION_LOG_LEVEL', 'INFO'),
    
    # Legacy debug mode
    'debug': os.environ.get('DICTATION_DEBUG', '').lower() in ('1', 'true', 'yes'),
}

# Legacy aliases for backwards compatibility
LOCK_FILE = CONFIG['lock_file']
TEMP_DIR = CONFIG['temp_dir']
SAMPLE_RATE = CONFIG['sample_rate']
CHANNELS = CONFIG['channels']
DTYPE = np.int16  # 16-bit PCM (not configurable)
MODEL_NAME = CONFIG['model']
DEVICE = CONFIG['device']
COMPUTE_TYPE = CONFIG['compute_type']
MODEL_CACHE = str(MODEL_CACHE_DIR)
XDOTOOL_DELAY_MS = CONFIG['typing_delay']
DEBUG_MODE = CONFIG['debug']


def process_text(text: str) -> str:
    """
    Apply text processing transformations based on CONFIG.
    
    Args:
        text: Raw transcription text
        
    Returns:
        Processed text with transformations applied
    """
    if not text:
        return text
    
    # Strip leading/trailing spaces
    if CONFIG['strip_leading']:
        text = text.lstrip()
    if CONFIG['strip_trailing']:
        text = text.rstrip()
    
    # Auto-capitalize first letter
    if CONFIG['auto_capitalize'] and len(text) > 0:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    return text


def transcribe_audio(audio_file: str, model_name: str = None, verbose: bool = False) -> str:
    """
    Transcribe audio file to text using faster-whisper.
    
    Args:
        audio_file: Path to WAV file (16kHz, mono recommended)
        model_name: Whisper model to use (tiny.en, base.en, small.en, medium.en)
        verbose: Show detailed timing and progress information
    
    Returns:
        Transcribed text as string
    
    Raises:
        FileNotFoundError: If audio file doesn't exist
        ImportError: If faster-whisper is not installed
        RuntimeError: If transcription fails
    """
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "faster-whisper is not installed.\n"
            "Install it with: pip install faster-whisper\n"
            "Or run: source scripts/setup-dev.sh dictation"
        )
    
    audio_path = Path(audio_file)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    if not audio_path.is_file():
        raise FileNotFoundError(f"Path is not a file: {audio_file}")
    
    # Use CONFIG if model_name not specified
    if model_name is None:
        model_name = CONFIG['model']
    
    device = CONFIG['device']
    compute_type = CONFIG['compute_type']
    language = CONFIG['language']
    beam_size = CONFIG['beam_size']
    temperature = CONFIG['temperature']
    vad_filter = CONFIG['vad_filter']
    initial_prompt = CONFIG['initial_prompt']
    
    # Send notification that transcription is starting
    _send_notification_static(
        "⏳ Transcribing...",
        "Processing your audio",
        urgency="normal"
    )
    
    start_time = time.time()
    
    try:
        if verbose:
            print(f"Loading Whisper model: {model_name}", file=sys.stderr)
            print(f"Device: {device}, Compute type: {compute_type}", file=sys.stderr)
        
        # Load Whisper model
        model = WhisperModel(
            model_size_or_path=model_name,
            device=device,
            compute_type=compute_type,
            cpu_threads=0,  # Use all available cores
            num_workers=1
        )
        
        load_time = time.time() - start_time
        if verbose:
            print(f"Model loaded in {load_time:.2f}s", file=sys.stderr)
        
        # Transcribe audio
        transcribe_start = time.time()
        transcribe_kwargs = {
            'language': language,
            'beam_size': beam_size,
            'temperature': temperature,
        }
        
        if vad_filter:
            transcribe_kwargs['vad_filter'] = True
            transcribe_kwargs['vad_parameters'] = dict(min_silence_duration_ms=500)
        
        if initial_prompt:
            transcribe_kwargs['initial_prompt'] = initial_prompt
        
        segments, info = model.transcribe(str(audio_path), **transcribe_kwargs)
        
        # Join segments into single string
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
        
        text = " ".join(text_parts)
        
        # Apply text processing
        text = process_text(text)
        
        transcribe_time = time.time() - transcribe_start
        total_time = time.time() - start_time
        
        if verbose:
            print(f"Transcription completed in {transcribe_time:.2f}s", file=sys.stderr)
            print(f"Total time: {total_time:.2f}s", file=sys.stderr)
            print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})", file=sys.stderr)
            if info.duration:
                print(f"Audio duration: {info.duration:.2f}s", file=sys.stderr)
                speed_ratio = info.duration / transcribe_time if transcribe_time > 0 else 0
                print(f"Processing speed: {speed_ratio:.1f}x realtime", file=sys.stderr)
        
        # Send completion notification
        if CONFIG['show_transcription']:
            _send_notification_static(
                "✅ Transcription Complete",
                text[:100] + ("..." if len(text) > 100 else ""),
                urgency="normal"
            )
        else:
            _send_notification_static(
                "✅ Transcription Complete",
                "Processing your audio",
                urgency="normal"
            )
        
        return text
        
    except Exception as e:
        error_msg = f"Transcription failed: {e}"
        _send_notification_static(
            "❌ Transcription Error",
            str(e),
            urgency="critical"
        )
        raise RuntimeError(error_msg) from e


def _send_notification_static(title, message, urgency="normal"):
    """
    Static helper function to send desktop notifications.
    Used by transcribe_audio() which is not part of a class.
    """
    if not CONFIG.get('enable_notifications', True):
        return
        
    try:
        tool = CONFIG.get('notification_tool', 'notify-send')
        urgency_arg = CONFIG.get('notification_urgency', urgency)
        
        subprocess.run(
            [tool, "-u", urgency_arg, title, message],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        # notify-send not available, silently ignore
        pass
    except Exception as e:
        print(f"Notification error: {e}", file=sys.stderr)


def paste_text_xdotool(text: str) -> bool:
    """
    Inject text at cursor position using xdotool.
    
    Args:
        text: Text to type at cursor position
        
    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False
        
    try:
        # Clear any stuck modifier keys (Ctrl, Alt, Shift)
        if CONFIG['clear_modifiers']:
            subprocess.run(
                ["xdotool", "keyup", "Control_L", "Alt_L", "Shift_L"],
                check=False,
                capture_output=True,
                timeout=5
            )
            # Small delay to ensure keys are released
            time.sleep(0.05)
        
        # Type the text
        # --clearmodifiers: ensure no modifiers interfere
        # --delay: milliseconds between keystrokes
        # --: end of options, everything after is literal text
        result = subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", str(CONFIG['typing_delay']), "--", text],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return True
        
    except subprocess.TimeoutExpired:
        _send_notification_static("❌ Dictation Error", "Text pasting timed out", urgency="critical")
        return False
    except FileNotFoundError:
        _send_notification_static("❌ Dictation Error", "xdotool not installed. Install with: sudo pacman -S xdotool", urgency="critical")
        return False
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else "Unknown error"
        _send_notification_static("❌ Dictation Error", f"xdotool failed: {error_msg}", urgency="critical")
        return False
    except Exception as e:
        _send_notification_static("❌ Dictation Error", f"Text injection error: {e}", urgency="critical")
        return False


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to clipboard as fallback when xdotool fails.
    
    Args:
        text: Text to copy to clipboard
        
    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False
        
    try:
        # Try xclip first (most common)
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode('utf-8'),
            check=True,
            capture_output=True,
            timeout=5
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try xsel as fallback
        try:
            subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=text.encode('utf-8'),
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # No clipboard tool available
            return False
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


class DictationRecorder:
    """Manages audio recording for dictation."""

    def __init__(self):
        self.audio_data = []
        self.stream = None
        self.recording = False
        self.audio_file = None
        self.started_at = None

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        # Copy audio data to our buffer
        self.audio_data.append(indata.copy())

    def _send_notification(self, title, message, urgency="normal"):
        """Send desktop notification using configured tool."""
        if not CONFIG.get('enable_notifications', True):
            return
            
        try:
            tool = CONFIG.get('notification_tool', 'notify-send')
            urgency_arg = CONFIG.get('notification_urgency', urgency)
            
            subprocess.run(
                [tool, "-u", urgency_arg, title, message],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            # notify-send not available, silently ignore
            pass
        except Exception as e:
            print(f"Notification error: {e}", file=sys.stderr)

    def _check_audio_device(self):
        """Check if audio input device is available."""
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            
            if default_input is None or default_input < 0:
                return False, "No default audio input device found"
            
            device_info = sd.query_devices(default_input)
            if device_info['max_input_channels'] < 1:
                return False, f"Device '{device_info['name']}' has no input channels"
            
            return True, device_info['name']
        except Exception as e:
            return False, str(e)

    def start_recording(self):
        """Start audio recording and create lock file."""
        # Check if already recording
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, 'r') as f:
                    lock_data = json.load(f)
                pid = lock_data.get('pid')
                
                # Check if the process is still running
                if pid and self._is_process_running(pid):
                    print(f"Error: Recording already in progress (PID: {pid})", file=sys.stderr)
                    self._send_notification(
                        "Dictation Error",
                        "Recording already in progress",
                        urgency="critical"
                    )
                    return 1
                else:
                    # Stale lock file, remove it
                    print("Removing stale lock file", file=sys.stderr)
                    LOCK_FILE.unlink()
            except (json.JSONDecodeError, KeyError, IOError):
                # Invalid lock file, remove it
                LOCK_FILE.unlink()

        # Check audio device availability
        device_available, device_info = self._check_audio_device()
        if not device_available:
            print(f"Error: Audio device error: {device_info}", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                f"Audio device error: {device_info}",
                urgency="critical"
            )
            return 1

        # Create temp directory if it doesn't exist
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error: Cannot create temp directory: {e}", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                f"Cannot create temp directory: {e}",
                urgency="critical"
            )
            return 1

        # Generate unique filename with PID and timestamp
        pid = os.getpid()
        timestamp = int(time.time())
        self.audio_file = TEMP_DIR / f"recording-{pid}-{timestamp}.wav"
        self.started_at = timestamp

        # Create lock file with recording metadata
        lock_data = {
            "pid": pid,
            "started_at": timestamp,
            "audio_file": str(self.audio_file),
            "stream_info": {
                "device": device_info,
                "sample_rate": SAMPLE_RATE,
                "channels": CHANNELS
            }
        }

        try:
            with open(LOCK_FILE, 'w') as f:
                json.dump(lock_data, f, indent=2)
        except IOError as e:
            print(f"Error: Cannot create lock file: {e}", file=sys.stderr)
            return 1

        # Register signal handlers for graceful termination
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start audio recording
        try:
            self.audio_data = []
            self.recording = True
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._audio_callback
            )
            self.stream.start()

            print(f"🎙️  Recording started (PID: {pid})")
            print(f"Device: {device_info}")
            print(f"Audio file: {self.audio_file}")
            print(f"Lock file: {LOCK_FILE}")
            print("\nPress Ctrl+C or run 'dictate.py --stop' to end recording")

            self._send_notification(
                "🎙️ Dictation",
                "Recording started...",
                urgency="normal"
            )

            # Keep the script running to continue recording
            # The recording happens in the callback thread
            while self.recording:
                time.sleep(0.1)

        except sd.PortAudioError as e:
            print(f"Error: Audio device error: {e}", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                f"Audio device error: {e}",
                urgency="critical"
            )
            # Clean up lock file
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            return 1
        except Exception as e:
            print(f"Error: Unexpected error during recording: {e}", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                f"Recording error: {e}",
                urgency="critical"
            )
            # Clean up lock file
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            return 1

        return 0

    def stop_recording(self):
        """Stop audio recording by signaling the recording process."""
        # Check if recording is in progress
        if not LOCK_FILE.exists():
            print("Error: No recording in progress", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                "No recording in progress",
                urgency="normal"
            )
            return 1

        # Read lock file to get recording process PID
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: Cannot read lock file: {e}", file=sys.stderr)
            # Try to clean up
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            return 1

        recording_pid = lock_data.get('pid')
        
        if not recording_pid:
            print("Error: Lock file does not contain PID", file=sys.stderr)
            LOCK_FILE.unlink()
            return 1

        # Check if the recording process is still running
        if not self._is_process_running(recording_pid):
            print(f"Error: Recording process (PID: {recording_pid}) is not running", file=sys.stderr)
            # Clean up stale lock file
            LOCK_FILE.unlink()
            return 1

        # Send SIGTERM to the recording process to trigger graceful shutdown
        try:
            print(f"Stopping recording process (PID: {recording_pid})...")
            os.kill(recording_pid, signal.SIGTERM)
            
            # Wait for the process to finish (up to 5 seconds)
            for i in range(50):
                if not self._is_process_running(recording_pid):
                    print("Recording stopped successfully")
                    return 0
                time.sleep(0.1)
            
            # If still running after 5 seconds, force kill
            if self._is_process_running(recording_pid):
                print("Process did not respond to SIGTERM, sending SIGKILL...", file=sys.stderr)
                os.kill(recording_pid, signal.SIGKILL)
                time.sleep(0.5)
                
                # Clean up lock file
                if LOCK_FILE.exists():
                    LOCK_FILE.unlink()
                
                return 1
                
        except ProcessLookupError:
            # Process already terminated
            print("Recording process already terminated")
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            return 0
        except Exception as e:
            print(f"Error stopping recording process: {e}", file=sys.stderr)
            return 1

        return 0

    def _is_process_running(self, pid):
        """Check if a process with given PID is running."""
        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _save_audio_data(self):
        """Save accumulated audio data to WAV file."""
        if not self.audio_data:
            print("Warning: No audio data captured", file=sys.stderr)
            return False
        
        try:
            # Concatenate all audio chunks
            audio_array = np.concatenate(self.audio_data, axis=0)

            # Save to WAV file
            with wave.open(str(self.audio_file), 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_array.tobytes())

            file_size = self.audio_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            duration = int(time.time() - self.started_at)

            print(f"✅ Recording stopped")
            print(f"Duration: {duration} seconds")
            print(f"Saved to: {self.audio_file}")
            print(f"File size: {file_size_mb:.2f} MB")

            self._send_notification(
                "✅ Dictation",
                f"Recording stopped ({duration}s)\nSaved to: {self.audio_file.name}",
                urgency="normal"
            )
            return True

        except Exception as e:
            print(f"Error: Failed to save audio file: {e}", file=sys.stderr)
            self._send_notification(
                "Dictation Error",
                f"Failed to save audio: {e}",
                urgency="critical"
            )
            return False

    def _signal_handler(self, signum, frame):
        """Handle termination signals by saving audio and exiting."""
        print("\n\nRecording interrupted by signal")
        self.recording = False
        
        # Stop the audio stream
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
        
        # Save audio data
        if self._save_audio_data():
            # Remove lock file
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            sys.exit(0)
        else:
            # Remove lock file even if save failed
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            sys.exit(1)


def cleanup_stale_lock():
    """Clean up stale lock file (from crashed process)."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            print("Cleaned up stale lock file", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not clean up lock file: {e}", file=sys.stderr)


def read_lock_file():
    """
    Read and parse lock file.
    
    Returns:
        dict: Lock file data, or None if file doesn't exist or is invalid
    """
    if not LOCK_FILE.exists():
        return None
        
    try:
        with open(LOCK_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Invalid lock file: {e}", file=sys.stderr)
        return None


def is_process_running(pid):
    """
    Check if a process with given PID is running.
    
    Args:
        pid: Process ID to check
        
    Returns:
        bool: True if process exists, False otherwise
    """
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def handle_toggle():
    """
    Handle toggle command: start if idle, stop+transcribe+paste if recording.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    lock_data = read_lock_file()
    
    if lock_data:
        # Currently recording - stop and process
        pid = lock_data.get('pid')
        audio_file = lock_data.get('audio_file')
        
        # Verify process is still running
        if pid and not is_process_running(pid):
            _send_notification_static(
                "🔧 Dictation",
                "Cleaning up stale recording session...",
                urgency="normal"
            )
            cleanup_stale_lock()
            return 0
        
        # Stop the recording
        recorder = DictationRecorder()
        stop_result = recorder.stop_recording()
        
        if stop_result != 0:
            _send_notification_static(
                "❌ Dictation Error",
                "Failed to stop recording",
                urgency="critical"
            )
            return stop_result
        
        # Wait briefly for file to be written
        time.sleep(0.2)
        
        # Verify audio file exists
        if not audio_file or not Path(audio_file).exists():
            _send_notification_static(
                "❌ Dictation Error",
                "Audio file not found",
                urgency="critical"
            )
            cleanup_stale_lock()
            return 1
        
        # Transcribe audio
        try:
            _send_notification_static(
                "⏳ Dictation",
                "Transcribing...",
                urgency="normal"
            )
            
            text = transcribe_audio(audio_file, verbose=False)
            
            if not text or not text.strip():
                _send_notification_static(
                    "⚠️ Dictation",
                    "No speech detected",
                    urgency="normal"
                )
                # Clean up
                cleanup_stale_lock()
                if not CONFIG.get('keep_temp', False) and Path(audio_file).exists():
                    Path(audio_file).unlink()
                return 0
            
            # Paste text
            word_count = len(text.split())
            _send_notification_static(
                "📝 Dictation",
                f"Pasting {word_count} words...",
                urgency="normal"
            )
            
            if paste_text_xdotool(text):
                _send_notification_static(
                    "✅ Dictation",
                    f"Done! Pasted {word_count} words",
                    urgency="normal"
                )
            else:
                # Fallback to clipboard
                if copy_to_clipboard(text):
                    _send_notification_static(
                        "⚠️ Dictation",
                        f"Text copied to clipboard ({word_count} words)\nPaste manually with Ctrl+V",
                        urgency="normal"
                    )
                else:
                    # Last resort: show in notification
                    preview = text[:100] + ("..." if len(text) > 100 else "")
                    _send_notification_static(
                        "⚠️ Dictation",
                        f"Could not paste or copy to clipboard.\nText: {preview}",
                        urgency="critical"
                    )
            
            # Clean up
            cleanup_stale_lock()
            if not CONFIG.get('keep_temp', False) and Path(audio_file).exists():
                try:
                    Path(audio_file).unlink()
                except Exception as e:
                    print(f"Warning: Could not delete audio file: {e}", file=sys.stderr)
            
            return 0
            
        except Exception as e:
            error_msg = str(e)
            _send_notification_static(
                "❌ Dictation Error",
                f"Transcription failed: {error_msg}",
                urgency="critical"
            )
            cleanup_stale_lock()
            return 1
    else:
        # Not recording - start recording
        recorder = DictationRecorder()
        return recorder.start_recording()


def main():
    """Main entry point for the dictation script."""
    parser = argparse.ArgumentParser(
        description="Core dictation script for audio recording and transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --start                              # Begin recording
  %(prog)s --stop                               # Stop recording and save
  %(prog)s --toggle                             # Toggle: start if idle, stop+paste if recording
  %(prog)s --transcribe audio.wav               # Transcribe audio file
  %(prog)s --transcribe audio.wav --model tiny.en  # Use faster model
  %(prog)s --transcribe audio.wav --verbose     # Show timing info

Lock file: /tmp/dictation.lock
Audio files: /tmp/dictation/
Model cache: ~/.cache/huggingface/hub/

Environment Variables:
  DICTATION_DEBUG=1                             # Keep audio files after transcription
        """
    )

    parser.add_argument(
        '--start',
        action='store_true',
        help='Start audio recording'
    )

    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop audio recording'
    )

    parser.add_argument(
        '--toggle',
        action='store_true',
        help='Toggle mode: start if idle, stop and paste text if recording'
    )

    parser.add_argument(
        '--transcribe',
        type=str,
        metavar='FILE',
        help='Transcribe audio file to text'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='base.en',
        choices=['tiny.en', 'base.en', 'small.en', 'medium.en'],
        help='Whisper model to use for transcription (default: base.en)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed timing and progress information'
    )

    args = parser.parse_args()

    # Validate arguments
    if sum([args.start, args.stop, args.toggle, bool(args.transcribe)]) > 1:
        print("Error: Can only use one of --start, --stop, --toggle, or --transcribe", file=sys.stderr)
        parser.print_help()
        return 1

    if not args.start and not args.stop and not args.toggle and not args.transcribe:
        print("Error: Must specify --start, --stop, --toggle, or --transcribe", file=sys.stderr)
        parser.print_help()
        return 1

    # Handle transcription
    if args.transcribe:
        try:
            text = transcribe_audio(
                args.transcribe,
                model_name=args.model,
                verbose=args.verbose
            )
            # Print transcribed text to stdout
            print(text)
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ImportError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Unexpected error during transcription: {e}", file=sys.stderr)
            return 1

    # Handle toggle mode
    if args.toggle:
        return handle_toggle()

    # Handle recording
    recorder = DictationRecorder()

    if args.start:
        return recorder.start_recording()
    elif args.stop:
        return recorder.stop_recording()

    return 0


if __name__ == "__main__":
    sys.exit(main())

