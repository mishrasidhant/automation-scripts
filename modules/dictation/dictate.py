#!/usr/bin/env python3
"""
Core dictation script for audio recording.

This script provides audio recording capabilities for the dictation system.
It uses sounddevice for audio capture and manages recording state via lock files.

Usage:
    python3 dictate.py --start    # Begin recording
    python3 dictate.py --stop     # Stop recording
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import wave
from pathlib import Path

# Check for required dependencies
try:
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required dependency: {e}", file=sys.stderr)
    print("\nPlease install required packages:", file=sys.stderr)
    print("  pip install sounddevice numpy", file=sys.stderr)
    print("\nSystem dependencies (Arch/Manjaro):", file=sys.stderr)
    print("  sudo pacman -S portaudio", file=sys.stderr)
    sys.exit(1)


# Configuration constants
LOCK_FILE = Path("/tmp/dictation.lock")
TEMP_DIR = Path("/tmp/dictation")
SAMPLE_RATE = 16000  # Hz - Optimal for Whisper transcription
CHANNELS = 1  # Mono audio
DTYPE = np.int16  # 16-bit PCM


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
        """Send desktop notification using notify-send."""
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, title, message],
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


def main():
    """Main entry point for the dictation script."""
    parser = argparse.ArgumentParser(
        description="Core dictation script for audio recording",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --start    # Begin recording
  %(prog)s --stop     # Stop recording and save

Lock file: /tmp/dictation.lock
Audio files: /tmp/dictation/
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

    args = parser.parse_args()

    # Validate arguments
    if args.start and args.stop:
        print("Error: Cannot use --start and --stop together", file=sys.stderr)
        parser.print_help()
        return 1

    if not args.start and not args.stop:
        print("Error: Must specify either --start or --stop", file=sys.stderr)
        parser.print_help()
        return 1

    recorder = DictationRecorder()

    if args.start:
        return recorder.start_recording()
    elif args.stop:
        return recorder.stop_recording()

    return 0


if __name__ == "__main__":
    sys.exit(main())

