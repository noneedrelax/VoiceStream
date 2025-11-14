# VoiceStream

VoiceStream is a lightweight, production-ready voice dictation application for Windows. It combines a floating UI with a system tray icon, leveraging OpenAI's Whisper API for transcription. The tool records audio in memory, avoiding disk I/O, and provides global hotkeys for quick operation.

## Features

- **Floating UI & System Tray Icon:**
  - A modern, draggable floating bar that's always on top for easy access.
  - A color-coded status indicator (blue for idle, red for recording, orange for transcribing).
  - A system tray icon with context menu options (Start, Stop & Transcribe, About/Help, Quit).

- **Real-time Voice Recording:**
  Start audio capture with a hotkey, the floating UI button, or through the system tray.

- **In-Memory Audio Processing:**
  Audio is captured and processed entirely in memory for speed and efficiency.

- **Accurate Transcription:**
  Uses OpenAI's Whisper API for high-quality speech-to-text conversion.

- **Global Hotkeys:**
  - `Ctrl+Shift+R` to toggle recording (start/stop).

- **Clipboard Integration:**
  Automatically copies and pastes the transcribed text into the active window.

- **Customizable Branding and Help:**
  An About/Help section providing your branding and support contact, accessible from both the floating UI and the tray icon.

## Installation

### Prerequisites

- **Python 3.6+**
  Ensure Python is installed on your Windows machine.

- **Required Python Packages:**
  Install the required packages using pip:

  ```bash
  pip install openai pyaudio pystray Pillow keyboard pyperclip
  ```

### Setup

Follow these steps to set up and run VoiceStream:

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/noneedrelax/VoiceStream.git
   cd VoiceStream
   ```

2. **Configure the API Key:**

   - Create a file named `apikey.txt` in the project root.
   - Paste your valid OpenAI API key into this file.
     *Example file content:*
     ```
     sk-YourActualAPIKeyHere
     ```

   > **Important:**
   > Make sure that `apikey.txt` is included in your `.gitignore` file so that it is not committed to the repository.

3. **(Optional) Create a Windows Command-Line Wrapper:**

   To run the tool without opening your IDE every time, create a batch file (e.g., `runVoiceStream.bat`) with the following content:

   ```batch
   @echo off
   cd /d "%~dp0"
   python dictate_with_hotkey.py
   pause
   ```

   Double-click the batch file to launch VoiceStream.

4. **Run the Application:**

   You can start VoiceStream directly from the command line by executing:

   ```bash
   python dictate_with_hotkey.py
   ```
