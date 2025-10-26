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

# Import the module under test
sys.path.insert(0, os.path.dirname(__file__))

# Temporarily disable import checks for testing
original_import = __builtins__.__import__

def mock_import(name, *args, **kwargs):
    if name in ['sounddevice', 'numpy', 'wave']:
        return MagicMock()
    return original_import(name, *args, **kwargs)

with patch('builtins.__import__', side_effect=mock_import):
    import dictate


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


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("Running Unit Tests for dictate.py")
    print("=" * 70)
    print("\nNote: Full integration tests require:")
    print("  pip install sounddevice numpy")
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
