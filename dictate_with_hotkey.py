import io
import openai
import pyaudio
import wave
import threading
import keyboard
import pyperclip
import time

from pystray import Icon, MenuItem as item
from PIL import Image, ImageDraw, ImageFont

# ------------------------------
# Configuration & API Key Loading
# ------------------------------
with open("apikey.txt", "r") as f:
    openai.api_key = f.read().strip()

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# Global flags & storage for audio
RECORDING = False
FRAMES = []

# ------------------------------
# In-Memory WAV Buffer Helper
# ------------------------------
class NamedBytesIO(io.BytesIO):
    def __init__(self, *args, name="audio.wav", **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

# ------------------------------
# Audio Recording Functions
# ------------------------------
def start_recording():
    global RECORDING, FRAMES
    RECORDING = True
    FRAMES = []

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

    while RECORDING:
        try:
            data = stream.read(CHUNK)
            FRAMES.append(data)
        except Exception:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

def stop_recording_and_transcribe():
    global RECORDING
    RECORDING = False
    time.sleep(0.5)  # Give a short time to ensure recording stops

    # Build an in-memory WAV file
    wav_buffer = NamedBytesIO()
    temp_audio = pyaudio.PyAudio()
    sample_width = temp_audio.get_sample_size(FORMAT)
    temp_audio.terminate()

    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(FRAMES))
    wav_buffer.seek(0)

    # Transcribe using OpenAI Whisper
    result = openai.Audio.transcribe("whisper-1", wav_buffer)
    text = result['text']

    # Copy text to clipboard and simulate paste (Ctrl+V)
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard.press_and_release('ctrl+v')

# ------------------------------
# Tray Icon Creation (with pystray & Pillow)
# ------------------------------
def generate_icon_image(text, bg_color, size=(64, 64)):
    """Generate an icon image with given text and background color."""
    image = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(image)
    try:
        # Try to use a modern sans-serif font
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    # Use textbbox to calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    pos = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(pos, text, font=font, fill="white")
    return image

# Create two icons:
# - Idle: Blue icon with "Mic" text
# - Recording: Green icon with "Rec" text
idle_icon_image = generate_icon_image("Mic", "#2196F3")
recording_icon_image = generate_icon_image("Rec", "#4CAF50")

# ------------------------------
# Tray Icon Menu Command Wrappers
# ------------------------------
def start_recording_wrapper(tray, _):
    # Update tray icon and start recording in a thread.
    tray.icon = recording_icon_image
    threading.Thread(target=start_recording, daemon=True).start()

def stop_recording_and_transcribe_wrapper(tray, _):
    # Stop recording and transcribe; then update tray icon back.
    stop_recording_and_transcribe()
    tray.icon = idle_icon_image

def quit_app(tray, _):
    tray.stop()

def show_about(tray, _):
    import tkinter as tk
    root = tk.Tk()
    root.title("About VoiceStream")
    tk.Label(root, text="VoiceStream\n\nDeveloped by Noneedrelax\nContact: noneedrelax@gmail.com", font=("Segoe UI", 12)).pack(padx=20, pady=20)
    tk.Button(root, text="Close", command=root.destroy).pack(pady=(0, 20))
    root.mainloop()

# ------------------------------
# Global Hotkeys (Keyboard)
# ------------------------------
def start_recording_hotkey():
    global tray_icon
    if tray_icon:
        tray_icon.icon = recording_icon_image
    threading.Thread(target=start_recording, daemon=True).start()

def stop_recording_and_transcribe_hotkey():
    global tray_icon
    stop_recording_and_transcribe()
    if tray_icon:
        tray_icon.icon = idle_icon_image

# Register the hotkeys.
keyboard.add_hotkey('ctrl+shift+r', start_recording_hotkey)
keyboard.add_hotkey('ctrl+shift+q', stop_recording_and_transcribe_hotkey)
# Start the keyboard listener in a daemon thread.
threading.Thread(target=lambda: keyboard.wait(), daemon=True).start()

# ------------------------------
# Create & Run Tray Icon
# ------------------------------
menu = (
    item('Start Recording', start_recording_wrapper),
    item('Stop and Transcribe', stop_recording_and_transcribe_wrapper),
    item('About/Help', show_about),
    item('Quit', quit_app)
)

tray_icon = Icon("DictationTool", idle_icon_image, "Dictation Tool", menu)
tray_icon.run()
