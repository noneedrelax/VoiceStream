import io
import openai
import pyaudio
import wave
import threading
import keyboard
import pyperclip
import time
import tkinter as tk
from tkinter import font as tkfont
from pystray import Icon, MenuItem as item
from PIL import Image, ImageDraw, ImageFont

# ------------------------------
# Configuration & API Key Loading
# ------------------------------
client = openai.OpenAI(api_key=open("apikey.txt", "r").read().strip())

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# Global flags & storage for audio
RECORDING = False
FRAMES = []
tray_icon = None

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
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=wav_buffer
    )
    text = result.text

    # Copy text to clipboard and simulate paste (Ctrl+V)
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard.press_and_release('ctrl+v')

# ------------------------------
# UI (Tkinter)
# ------------------------------
class VoiceStreamApp:
    def __init__(self, root, quit_callback):
        self.root = root
        self.quit_callback = quit_callback
        self.root.title("VoiceStream")
        
        # Calculate position for bottom-right
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 200
        window_height = 30
        padding = 10
        x = screen_width - window_width - padding
        y = screen_height - window_height - padding - 80
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.overrideredirect(True) # Remove window decorations

        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)

        self.status_canvas = tk.Canvas(root, width=20, height=20, bg="blue", highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=5)

        self.record_button = tk.Button(root, text="Record", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.pin_button = tk.Button(root, text="Pin", command=self.toggle_always_on_top)
        self.pin_button.pack(side=tk.LEFT, padx=5)

        # Context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="About", command=self.show_about)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Quit", command=self.quit_callback)

        self.root.bind("<Button-3>", self.show_context_menu)
        
        # Make window draggable
        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<ButtonRelease-1>", self.stop_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # Hotkey
        keyboard.add_hotkey('ctrl+shift+r', self.toggle_recording)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About VoiceStream")
        tk.Label(about_window, text="VoiceStream\n\nDeveloped by Noneedrelax\nContact: noneedrelax@gmail.com", font=("Segoe UI", 12)).pack(padx=20, pady=20)
        tk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=(0, 20))

    def toggle_always_on_top(self):
        self.always_on_top.set(not self.always_on_top.get())
        self.root.attributes("-topmost", self.always_on_top.get())
        self.pin_button.config(text="Unpin" if self.always_on_top.get() else "Pin")

    def toggle_recording(self):
        if not RECORDING:
            self.start_recording_ui()
        else:
            self.stop_transcribe_ui()

    def start_recording_ui(self):
        global tray_icon
        self.status_canvas.config(bg="red")
        self.record_button.config(text="Stop")
        if tray_icon:
            tray_icon.icon = recording_icon_image
        threading.Thread(target=start_recording, daemon=True).start()

    def stop_transcribe_ui(self):
        self.status_canvas.config(bg="orange")
        self.record_button.config(text="Record", state=tk.DISABLED)
        
        threading.Thread(target=self.transcribe_and_update_ui, daemon=True).start()

    def transcribe_and_update_ui(self):
        global tray_icon
        stop_recording_and_transcribe()
        if tray_icon:
            tray_icon.icon = idle_icon_image
        self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.status_canvas.config(bg="blue")
        self.record_button.config(text="Record", state=tk.NORMAL)

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

def quit_app(icon=None, item=None):
    if icon:
        icon.stop()
    root.quit()

def show_about_tray(icon, item):
    app.show_about()

def start_recording_wrapper():
    app.start_recording_ui()

def stop_recording_and_transcribe_wrapper():
    app.stop_transcribe_ui()

# ------------------------------
# Main Execution
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceStreamApp(root, quit_app)
    
    menu = (
        item('Start Recording', start_recording_wrapper),
        item('Stop and Transcribe', stop_recording_and_transcribe_wrapper),
        item('About/Help', show_about_tray),
        item('Quit', quit_app)
    )
    tray_icon = Icon("DictationTool", idle_icon_image, "Dictation Tool", menu)

    def run_tray_icon():
        tray_icon.run()

    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()
    
    # Start the keyboard listener in a daemon thread.
    threading.Thread(target=lambda: keyboard.wait(), daemon=True).start()
    root.mainloop()
