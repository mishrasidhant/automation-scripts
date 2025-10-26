import sounddevice as sd
import numpy as np
import wave
import keyboard
import threading
import subprocess
import os
import tempfile

# === CONFIG ===
HOTKEY = "ctrl+alt+space"
WHISPER_PATH = "/path/to/whisper.cpp/main"  # path to your whisper.cpp executable
MODEL_PATH = "/path/to/models/ggml-base.en.bin"  # or any other model file
SAMPLE_RATE = 16000
CHANNELS = 1
recording = False
frames = []

def record_audio():
    global frames, recording
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
        while recording:
            data, _ = stream.read(1024)
            frames.append(data.copy())

def save_wav(filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

def transcribe_with_whisper(file_path):
    print("Transcribing with whisper.cpp...")
    cmd = [
        WHISPER_PATH,
        "-m", MODEL_PATH,
        "-f", file_path,
        "-nt",  # no timestamps
        "-l", "en"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    text = result.stdout.strip()
    print("Transcribed:", text)
    return text

def paste_text(text):
    subprocess.run(["xdotool", "type", "--clearmodifiers", text])

def toggle_recording():
    global recording
    if not recording:
        print("🎙️ Recording started... (press Ctrl+Alt+Space to stop)")
        os.system('notify-send "Dictation" "Recording started..."')
        recording = True
        threading.Thread(target=record_audio, daemon=True).start()
    else:
        print("🛑 Recording stopped.")
        os.system('notify-send "Dictation" "Transcribing..."')
        recording = False
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            filename = tmpfile.name
        save_wav(filename)
        text = transcribe_with_whisper(filename)
        paste_text(text)
        os.remove(filename)
        os.system('notify-send "Dictation" "Transcription complete."')

keyboard.add_hotkey(HOTKEY, toggle_recording)

print(f"✅ Dictation ready. Press {HOTKEY} to start/stop.")
keyboard.wait()  # keeps program running
