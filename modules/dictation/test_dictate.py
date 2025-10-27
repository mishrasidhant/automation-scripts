#!/usr/bin/env python3
"""
Unit tests for dictate.py

These tests can run without sounddevice installed for CI/CD.
For full integration tests, install dependencies first:
    pip install sounddevice numpy

Run with: python3 test_dictate.py
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock optional dependencies before import
if 'sounddevice' not in sys.modules:
    sys.modules['sounddevice'] = MagicMock()
if 'numpy' not in sys.modules:
    mock_np = MagicMock()
    mock_np.int16 = 'int16'
    mock_np.concatenate = MagicMock(return_value=MagicMock(tobytes=MagicMock(return_value=b'')))
    sys.modules['numpy'] = mock_np
if 'faster_whisper' not in sys.modules:
    sys.modules['faster_whisper'] = MagicMock()

# Import the module under test
sys.path.insert(0, os.path.dirname(__file__))

# Handle different Python versions for __builtins__
if isinstance(__builtins__, dict):
    # Python 3.10+
    original_import = __builtins__['__import__']
    
    def mock_import(name, *args, **kwargs):
        if name in ['sounddevice', 'numpy', 'wave']:
            return MagicMock()
        return original_import(name, *args, **kwargs)
    
    __builtins__['__import__'] = mock_import
    import dictate
    __builtins__['__import__'] = original_import
else:
    # Python < 3.10
    original_import = __builtins__.__import__
    
    def mock_import(name, *args, **kwargs):
        if name in ['sounddevice', 'numpy', 'wave']:
            return MagicMock()
        return original_import(name, *args, **kwargs)
    
    __builtins__.__import__ = mock_import
    import dictate
    __builtins__.__import__ = original_import


class TestLockFileManagement(unittest.TestCase):
    """Test lock file creation and management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_lock_file = Path(self.temp_dir) / "test.lock"
        self.test_audio_dir = Path(self.temp_dir) / "audio"
        self.test_audio_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_lock_file.exists():
            self.test_lock_file.unlink()
        
        for file in self.test_audio_dir.glob("*"):
            if file.is_file():
                file.unlink()
        
        if self.test_audio_dir.exists():
            self.test_audio_dir.rmdir()
        
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    def test_lock_file_format(self):
        """Test that lock file can be created with correct JSON format."""
        # Create a sample lock file
        pid = os.getpid()
        timestamp = int(time.time())
        audio_file = self.test_audio_dir / f"recording-{pid}.wav"
        
        lock_data = {
            "pid": pid,
            "started_at": timestamp,
            "audio_file": str(audio_file),
            "stream_info": {
                "device": "Test Device",
                "sample_rate": 16000,
                "channels": 1
            }
        }
        
        # Write lock file
        with open(self.test_lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        # Verify it exists and is valid JSON
        self.assertTrue(self.test_lock_file.exists())
        
        with open(self.test_lock_file, 'r') as f:
            loaded_data = json.load(f)
        
        # Verify structure
        self.assertEqual(loaded_data['pid'], pid)
        self.assertEqual(loaded_data['started_at'], timestamp)
        self.assertEqual(loaded_data['audio_file'], str(audio_file))
        self.assertIn('stream_info', loaded_data)
        self.assertEqual(loaded_data['stream_info']['sample_rate'], 16000)
        self.assertEqual(loaded_data['stream_info']['channels'], 1)

    def test_lock_file_indicates_recording_state(self):
        """Test that presence of lock file indicates recording state."""
        # No lock file = not recording
        self.assertFalse(self.test_lock_file.exists())
        
        # Create lock file = recording
        lock_data = {"pid": os.getpid(), "started_at": int(time.time())}
        with open(self.test_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        self.assertTrue(self.test_lock_file.exists())
        
        # Remove lock file = stopped recording
        self.test_lock_file.unlink()
        self.assertFalse(self.test_lock_file.exists())


class TestProcessChecking(unittest.TestCase):
    """Test process running detection."""

    def test_is_process_running_current_process(self):
        """Test that current process is detected as running."""
        recorder = dictate.DictationRecorder()
        current_pid = os.getpid()
        
        is_running = recorder._is_process_running(current_pid)
        self.assertTrue(is_running, "Current process should be detected as running")

    def test_is_process_running_invalid_pid(self):
        """Test that invalid PID is detected as not running."""
        recorder = dictate.DictationRecorder()
        invalid_pid = 999999  # Very unlikely to exist
        
        is_running = recorder._is_process_running(invalid_pid)
        self.assertFalse(is_running, "Invalid PID should not be detected as running")


class TestAudioConfiguration(unittest.TestCase):
    """Test audio configuration constants."""

    def test_sample_rate_whisper_compatible(self):
        """Test that sample rate is 16kHz (Whisper requirement)."""
        self.assertEqual(dictate.SAMPLE_RATE, 16000)

    def test_channels_mono(self):
        """Test that audio is mono (1 channel)."""
        self.assertEqual(dictate.CHANNELS, 1)

    def test_lock_file_location(self):
        """Test that lock file is in /tmp."""
        self.assertEqual(str(dictate.LOCK_FILE), "/tmp/dictation.lock")

    def test_temp_dir_location(self):
        """Test that temp directory is /tmp/dictation."""
        self.assertEqual(str(dictate.TEMP_DIR), "/tmp/dictation")


class TestCLIArguments(unittest.TestCase):
    """Test command-line argument parsing."""

    def test_no_arguments_shows_error(self):
        """Test that running without arguments returns error code."""
        with patch('sys.argv', ['dictate.py']):
            result = dictate.main()
            self.assertEqual(result, 1)

    def test_conflicting_arguments(self):
        """Test that --start and --stop together shows error."""
        with patch('sys.argv', ['dictate.py', '--start', '--stop']):
            result = dictate.main()
            self.assertEqual(result, 1)

    @patch('dictate.DictationRecorder.start_recording', return_value=0)
    def test_start_argument(self, mock_start):
        """Test that --start calls start_recording."""
        with patch('sys.argv', ['dictate.py', '--start']):
            result = dictate.main()
        
        mock_start.assert_called_once()
        self.assertEqual(result, 0)

    @patch('dictate.DictationRecorder.stop_recording', return_value=0)
    def test_stop_argument(self, mock_stop):
        """Test that --stop calls stop_recording."""
        with patch('sys.argv', ['dictate.py', '--stop']):
            result = dictate.main()
        
        mock_stop.assert_called_once()
        self.assertEqual(result, 0)


class TestNotifications(unittest.TestCase):
    """Test notification functionality."""

    @patch('dictate.subprocess.run')
    def test_notification_calls_notify_send(self, mock_run):
        """Test that notifications use notify-send."""
        recorder = dictate.DictationRecorder()
        recorder._send_notification("Test Title", "Test Message", "normal")
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        
        self.assertEqual(call_args[0], "notify-send")
        self.assertIn("Test Title", call_args)
        self.assertIn("Test Message", call_args)

    @patch('dictate.subprocess.run', side_effect=FileNotFoundError)
    def test_notification_handles_missing_notify_send(self, mock_run):
        """Test that missing notify-send doesn't crash."""
        recorder = dictate.DictationRecorder()
        
        # Should not raise exception
        try:
            recorder._send_notification("Test", "Message")
        except FileNotFoundError:
            self.fail("Should handle missing notify-send gracefully")


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def test_stop_without_lock_file(self):
        """Test stopping when no recording is in progress."""
        temp_dir = tempfile.mkdtemp()
        test_lock = Path(temp_dir) / "nonexistent.lock"
        
        with patch.object(dictate, 'LOCK_FILE', test_lock):
            recorder = dictate.DictationRecorder()
            result = recorder.stop_recording()
        
        self.assertEqual(result, 1, "Should return error when not recording")
        os.rmdir(temp_dir)

    def test_invalid_lock_file_handled(self):
        """Test that corrupted lock file is handled gracefully."""
        temp_dir = tempfile.mkdtemp()
        test_lock = Path(temp_dir) / "corrupt.lock"
        
        # Create invalid JSON
        with open(test_lock, 'w') as f:
            f.write("invalid json{{{")
        
        with patch.object(dictate, 'LOCK_FILE', test_lock):
            recorder = dictate.DictationRecorder()
            result = recorder.stop_recording()
        
        self.assertEqual(result, 1, "Should handle corrupt lock file")
        
        # Clean up - file may have been deleted by the function
        if test_lock.exists():
            test_lock.unlink()
        os.rmdir(temp_dir)


class TestTranscriptionFunction(unittest.TestCase):
    """Test transcription functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = Path(self.temp_dir) / "test_audio.wav"
        # Create a dummy audio file for testing
        self.test_audio_file.touch()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_audio_file.exists():
            self.test_audio_file.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    def test_transcribe_missing_file(self):
        """Test that transcription fails gracefully with missing file."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.wav"
        
        with patch.object(dictate, 'WHISPER_AVAILABLE', True):
            with self.assertRaises(FileNotFoundError):
                dictate.transcribe_audio(str(nonexistent_file))

    def test_transcribe_without_whisper_installed(self):
        """Test that transcription fails when faster-whisper not installed."""
        with patch.object(dictate, 'WHISPER_AVAILABLE', False):
            with self.assertRaises(ImportError) as context:
                dictate.transcribe_audio(str(self.test_audio_file))
            
            self.assertIn("faster-whisper", str(context.exception))

    @patch('dictate.WhisperModel')
    @patch('dictate._send_notification_static')
    def test_transcribe_success(self, mock_notify, mock_whisper_model):
        """Test successful transcription."""
        # Mock the transcription result
        mock_segment_1 = MagicMock()
        mock_segment_1.text = "This is a test."
        mock_segment_2 = MagicMock()
        mock_segment_2.text = "Another sentence."
        
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.98
        mock_info.duration = 5.0
        
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = (
            [mock_segment_1, mock_segment_2],
            mock_info
        )
        mock_whisper_model.return_value = mock_model_instance
        
        with patch.object(dictate, 'WHISPER_AVAILABLE', True):
            result = dictate.transcribe_audio(str(self.test_audio_file))
        
        self.assertEqual(result, "This is a test. Another sentence.")
        mock_whisper_model.assert_called_once()
        # Check notifications were sent (start and completion)
        self.assertEqual(mock_notify.call_count, 2)

    @patch('dictate.WhisperModel')
    @patch('dictate._send_notification_static')
    def test_transcribe_with_model_selection(self, mock_notify, mock_whisper_model):
        """Test transcription with different model selection."""
        mock_segment = MagicMock()
        mock_segment.text = "Test"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_info.duration = 2.0
        
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model_instance
        
        with patch.object(dictate, 'WHISPER_AVAILABLE', True):
            result = dictate.transcribe_audio(str(self.test_audio_file), model_name="tiny.en")
        
        # Verify correct model was requested
        call_kwargs = mock_whisper_model.call_args[1]
        self.assertEqual(call_kwargs['model_size_or_path'], "tiny.en")
        self.assertEqual(result, "Test")

    @patch('dictate.WhisperModel')
    @patch('dictate._send_notification_static')
    def test_transcribe_empty_audio(self, mock_notify, mock_whisper_model):
        """Test transcription of silent/empty audio."""
        # Mock empty transcription result
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.5
        mock_info.duration = 1.0
        
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([], mock_info)
        mock_whisper_model.return_value = mock_model_instance
        
        with patch.object(dictate, 'WHISPER_AVAILABLE', True):
            result = dictate.transcribe_audio(str(self.test_audio_file))
        
        self.assertEqual(result, "")

    @patch('dictate.WhisperModel', side_effect=Exception("Model load failed"))
    @patch('dictate._send_notification_static')
    def test_transcribe_model_load_failure(self, mock_notify, mock_whisper_model):
        """Test transcription handles model loading errors."""
        with patch.object(dictate, 'WHISPER_AVAILABLE', True):
            with self.assertRaises(RuntimeError):
                dictate.transcribe_audio(str(self.test_audio_file))
        
        # Verify error notification was sent
        error_calls = [call for call in mock_notify.call_args_list if "Error" in str(call)]
        self.assertGreater(len(error_calls), 0)


class TestTranscriptionCLI(unittest.TestCase):
    """Test transcription command-line interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = Path(self.temp_dir) / "test.wav"
        self.test_audio_file.touch()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_audio_file.exists():
            self.test_audio_file.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    @patch('dictate.transcribe_audio', return_value="Transcribed text")
    def test_transcribe_cli_argument(self, mock_transcribe):
        """Test that --transcribe argument calls transcribe_audio."""
        with patch('sys.argv', ['dictate.py', '--transcribe', str(self.test_audio_file)]):
            result = dictate.main()
        
        mock_transcribe.assert_called_once()
        self.assertEqual(result, 0)

    @patch('dictate.transcribe_audio', return_value="Test output")
    def test_transcribe_with_model_option(self, mock_transcribe):
        """Test --transcribe with --model option."""
        with patch('sys.argv', ['dictate.py', '--transcribe', str(self.test_audio_file), '--model', 'tiny.en']):
            result = dictate.main()
        
        call_kwargs = mock_transcribe.call_args[1]
        self.assertEqual(call_kwargs['model_name'], 'tiny.en')
        self.assertEqual(result, 0)

    @patch('dictate.transcribe_audio', return_value="Verbose test")
    def test_transcribe_with_verbose_option(self, mock_transcribe):
        """Test --transcribe with --verbose option."""
        with patch('sys.argv', ['dictate.py', '--transcribe', str(self.test_audio_file), '--verbose']):
            result = dictate.main()
        
        call_kwargs = mock_transcribe.call_args[1]
        self.assertTrue(call_kwargs['verbose'])
        self.assertEqual(result, 0)

    def test_conflicting_transcribe_and_start(self):
        """Test that --transcribe and --start together shows error."""
        with patch('sys.argv', ['dictate.py', '--start', '--transcribe', str(self.test_audio_file)]):
            result = dictate.main()
            self.assertEqual(result, 1)

    @patch('dictate.transcribe_audio', side_effect=FileNotFoundError("File not found"))
    def test_transcribe_cli_file_not_found(self, mock_transcribe):
        """Test CLI handles file not found error."""
        with patch('sys.argv', ['dictate.py', '--transcribe', 'nonexistent.wav']):
            result = dictate.main()
        
        self.assertEqual(result, 1)


class TestLoadConfig(unittest.TestCase):
    """Test configuration loading from environment variables."""

    def test_load_config_defaults(self):
        """Test that load_config returns sensible defaults when no env vars are set."""
        # Clear environment to test defaults
        with patch.dict(os.environ, {}, clear=True):
            config = dictate.load_config()
            
        self.assertEqual(config['model'], 'base.en')
        self.assertEqual(config['device'], 'cpu')
        self.assertEqual(config['compute_type'], 'int8')
        self.assertEqual(config['sample_rate'], 16000)
        self.assertEqual(config['channels'], 1)
        self.assertEqual(config['typing_delay'], 12)
        self.assertFalse(config['debug'])
        self.assertTrue(config['vad_filter'])

    def test_load_config_from_env(self):
        """Test that load_config reads from environment variables."""
        with patch.dict(os.environ, {'DICTATION_WHISPER_MODEL': 'tiny.en', 'DICTATION_TYPING_DELAY': '20'}):
            config = dictate.load_config()
            
        self.assertEqual(config['model'], 'tiny.en')
        self.assertEqual(config['typing_delay'], 20)

    def test_load_config_invalid_model(self):
        """Test that invalid model is rejected with ValueError."""
        with patch.dict(os.environ, {'DICTATION_WHISPER_MODEL': 'invalid_model'}):
            with self.assertRaises(ValueError):
                dictate.load_config()

    def test_load_config_invalid_device(self):
        """Test that invalid device is rejected with ValueError."""
        with patch.dict(os.environ, {'DICTATION_WHISPER_DEVICE': 'invalid_device'}):
            with self.assertRaises(ValueError):
                dictate.load_config()

    def test_load_config_boolean_handling(self):
        """Test that boolean environment variables are parsed correctly."""
        with patch.dict(os.environ, {'DICTATION_WHISPER_VAD_FILTER': 'false', 'DICTATION_ENABLE_NOTIFICATIONS': 'false'}):
            config = dictate.load_config()
            
        self.assertFalse(config['vad_filter'])
        self.assertFalse(config['enable_notifications'])

    def test_load_config_numeric_handling(self):
        """Test that numeric environment variables are converted correctly."""
        with patch.dict(os.environ, {'DICTATION_SAMPLE_RATE': '8000', 'DICTATION_CHANNELS': '2', 'DICTATION_TYPING_DELAY': '50'}):
            config = dictate.load_config()
            
        self.assertEqual(config['sample_rate'], 8000)
        self.assertEqual(config['channels'], 2)
        self.assertEqual(config['typing_delay'], 50)


class TestTranscriptionConfiguration(unittest.TestCase):
    """Test transcription configuration constants."""

    def test_default_model_is_base_en(self):
        """Test that default model is base.en for balanced performance."""
        self.assertEqual(dictate.CONFIG['model'], "base.en")

    def test_device_is_cpu(self):
        """Test that default device is CPU (no GPU required)."""
        self.assertEqual(dictate.CONFIG['device'], "cpu")

    def test_compute_type_optimized(self):
        """Test that compute type is int8 for CPU optimization."""
        self.assertEqual(dictate.CONFIG['compute_type'], "int8")

    def test_model_cache_location(self):
        """Test that model cache points to huggingface hub."""
        cache_path = dictate.MODEL_CACHE
        self.assertIn(".cache/huggingface", cache_path)


class TestTextInjection(unittest.TestCase):
    """Test text injection and clipboard functionality."""

    @patch('dictate.subprocess.run')
    def test_paste_text_xdotool_success(self, mock_run):
        """Test successful text pasting with xdotool."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = dictate.paste_text_xdotool("Test text")
        
        self.assertTrue(result)
        # Should call keyup first, then type
        self.assertEqual(mock_run.call_count, 2)
        
        # Verify xdotool type was called with correct arguments
        type_call = mock_run.call_args_list[1]
        self.assertIn("xdotool", type_call[0][0])
        self.assertIn("type", type_call[0][0])
        self.assertIn("Test text", type_call[0][0])

    @patch('dictate.subprocess.run', side_effect=FileNotFoundError)
    @patch('dictate._send_notification_static')
    def test_paste_text_xdotool_not_installed(self, mock_notify, mock_run):
        """Test that missing xdotool is handled gracefully."""
        result = dictate.paste_text_xdotool("Test text")
        
        self.assertFalse(result)
        # Should notify user about missing xdotool
        mock_notify.assert_called()
        call_args = mock_notify.call_args[0]
        self.assertIn("xdotool", str(call_args))

    def test_paste_text_xdotool_empty_text(self):
        """Test that empty text returns False."""
        result = dictate.paste_text_xdotool("")
        self.assertFalse(result)
        
        result = dictate.paste_text_xdotool(None)
        self.assertFalse(result)

    @patch('dictate.subprocess.run')
    def test_copy_to_clipboard_xclip_success(self, mock_run):
        """Test clipboard copy with xclip."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = dictate.copy_to_clipboard("Test text")
        
        self.assertTrue(result)
        call_args = mock_run.call_args[0][0]
        self.assertIn("xclip", call_args)

    @patch('dictate.subprocess.run', side_effect=[
        subprocess.CalledProcessError(1, 'xclip'),
        MagicMock(returncode=0)
    ])
    def test_copy_to_clipboard_xsel_fallback(self, mock_run):
        """Test clipboard copy falls back to xsel if xclip fails."""
        result = dictate.copy_to_clipboard("Test text")
        
        self.assertTrue(result)
        # Should have tried both xclip and xsel
        self.assertEqual(mock_run.call_count, 2)
        
        # Second call should be xsel
        xsel_call = mock_run.call_args[0][0]
        self.assertIn("xsel", xsel_call)

    @patch('dictate.subprocess.run', side_effect=[
        FileNotFoundError,
        FileNotFoundError
    ])
    def test_copy_to_clipboard_no_tools_available(self, mock_run):
        """Test clipboard copy fails gracefully when no tools available."""
        result = dictate.copy_to_clipboard("Test text")
        
        self.assertFalse(result)


class TestToggleMode(unittest.TestCase):
    """Test toggle mode functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_lock_file = Path(self.temp_dir) / "test.lock"
        self.test_audio_file = Path(self.temp_dir) / "test.wav"
        self.test_audio_file.touch()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_audio_file.exists():
            self.test_audio_file.unlink()
        if self.test_lock_file.exists():
            self.test_lock_file.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    def test_read_lock_file_valid(self):
        """Test reading valid lock file."""
        lock_data = {"pid": 12345, "audio_file": "/tmp/test.wav"}
        with open(self.test_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            result = dictate.read_lock_file()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['pid'], 12345)

    def test_read_lock_file_missing(self):
        """Test reading non-existent lock file."""
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            result = dictate.read_lock_file()
        
        self.assertIsNone(result)

    def test_read_lock_file_invalid_json(self):
        """Test reading corrupted lock file."""
        with open(self.test_lock_file, 'w') as f:
            f.write("invalid json{{{")
        
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            result = dictate.read_lock_file()
        
        self.assertIsNone(result)

    def test_is_process_running_current(self):
        """Test checking if current process is running."""
        current_pid = os.getpid()
        result = dictate.is_process_running(current_pid)
        self.assertTrue(result)

    def test_is_process_running_invalid(self):
        """Test checking invalid process ID."""
        result = dictate.is_process_running(999999)
        self.assertFalse(result)

    def test_cleanup_stale_lock(self):
        """Test cleaning up stale lock file."""
        self.test_lock_file.touch()
        
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            dictate.cleanup_stale_lock()
        
        self.assertFalse(self.test_lock_file.exists())

    @patch('dictate.DictationRecorder.start_recording', return_value=0)
    def test_handle_toggle_start_when_idle(self, mock_start):
        """Test toggle starts recording when idle."""
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            result = dictate.handle_toggle()
        
        mock_start.assert_called_once()
        self.assertEqual(result, 0)

    @patch('dictate.is_process_running', return_value=False)
    @patch('dictate.cleanup_stale_lock')
    @patch('dictate._send_notification_static')
    def test_handle_toggle_cleans_stale_lock(self, mock_notify, mock_cleanup, mock_running):
        """Test toggle cleans up stale lock file."""
        # Create stale lock file
        lock_data = {"pid": 99999, "audio_file": str(self.test_audio_file)}
        with open(self.test_lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        with patch.object(dictate, 'LOCK_FILE', self.test_lock_file):
            result = dictate.handle_toggle()
        
        mock_cleanup.assert_called_once()
        self.assertEqual(result, 0)


class TestToggleCLI(unittest.TestCase):
    """Test toggle mode CLI integration."""

    @patch('dictate.handle_toggle', return_value=0)
    def test_toggle_cli_argument(self, mock_toggle):
        """Test that --toggle argument calls handle_toggle."""
        with patch('sys.argv', ['dictate.py', '--toggle']):
            result = dictate.main()
        
        mock_toggle.assert_called_once()
        self.assertEqual(result, 0)

    def test_conflicting_toggle_and_start(self):
        """Test that --toggle and --start together shows error."""
        with patch('sys.argv', ['dictate.py', '--toggle', '--start']):
            result = dictate.main()
            self.assertEqual(result, 1)

    def test_conflicting_toggle_and_transcribe(self):
        """Test that --toggle and --transcribe together shows error."""
        with patch('sys.argv', ['dictate.py', '--toggle', '--transcribe', 'test.wav']):
            result = dictate.main()
            self.assertEqual(result, 1)


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("Running Unit Tests for dictate.py")
    print("=" * 70)
    print("\nNote: Full integration tests require:")
    print("  pip install sounddevice numpy faster-whisper")
    print("  sudo pacman -S portaudio")
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLockFileManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessChecking))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIArguments))
    suite.addTests(loader.loadTestsFromTestCase(TestNotifications))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptionFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptionCLI))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptionConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestTextInjection))
    suite.addTests(loader.loadTestsFromTestCase(TestToggleMode))
    suite.addTests(loader.loadTestsFromTestCase(TestToggleCLI))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
