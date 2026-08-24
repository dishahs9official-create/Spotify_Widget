# 🎵 Spotify Desktop Widget

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-brightgreen.svg)](https://pypi.org/project/PySide6/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A gorgeous, lightweight, and highly customizable desktop media widget for Windows. Integrates natively with the Windows Global System Media Transport Controls (GSMTC) to display and control playing music.

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage-and-customization) • [How It Works](#-how-it-works) • [Troubleshooting](#-troubleshooting)

</div>

---

## 📸 Preview

<div align="center">
  <img src="screenshot.png" alt="Spotify Desktop Widget Preview" width="450px" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);"/>
</div>
<img width="936" height="530" alt="image" src="https://github.com/user-attachments/assets/44ab8ba1-0048-4ade-aeed-5d495fdf5319" />

---

## ✨ Features

*   **🎨 Dynamic Adaptive Background**: Automatically extracts the dominant/average color of the current track's album art in real-time and blends it into a semi-transparent dark gradient that matches Spotify's mobile layout.
*   **🖱️ Two Stable Window Modes**:
    *   **Desktop Mode (Default)**: Pinned directly to the desktop wallpaper background. It stays behind all your active windows (Chrome, IDE, folders) so it never blocks your work, and remains interactive.
    *   **Float Mode**: Always stays on top of all application windows.
*   **🛠️ Right-Click Settings Menu**: Right-click anywhere on the widget to access all customization options instantly (no complex config files needed).
*   **🎛️ Background Opacity Control**: Adjust the transparency of the background card from a glass-like `15%` up to a solid `100%`.
*   **🎨 Custom Color Picker**: Turn off dynamic color matching and select any solid custom color using a native Windows color selection dialog.
*   **💚 Interactive Heart**: Toggle a Spotify-green heart button.
*   **💾 Settings & Position Memory**: Remembers your preferred mode, color, opacity, and the exact coordinates where you dragged the widget on your screen.
*   **⚙️ Auto-Start on Boot**: Automatically launches silently on Windows boot, keeping it persistent on your desktop background.

---

## 📦 Installation

### 1. Prerequisites
Make sure you have [Python 3.10 or newer](https://www.python.org/downloads/) installed. During installation, ensure the box **"Add Python to PATH"** is checked.

### 2. Clone and Install Dependencies
Clone this repository (or download the ZIP) and install the dependencies from the project root:

```bash
pip install -r requirements.txt
```

### 3. Running the Widget
Run the widget using Python:

```bash
python widget.py
```
*Note: To run the widget silently in the background without opening a command prompt window, use `pythonw widget.py`.*

---

## 🎮 Usage and Customization

*   **Positioning**: Drag the widget by clicking and holding **any dark background area** to slide it anywhere on your screens.
*   **Switching Modes**: Click the pin icon (**📌**) in the top right to cycle between **Desktop Mode** (behind active tabs) and **Float Mode** (always on top).
*   **Right-Click Customizations**: Right-click the widget to:
    *   Turn **Match Album Color (Dynamic)** on or off.
    *   Click **Pick Custom Color...** to select your own solid theme.
    *   Select **Background Opacity** presets (15%, 30%, 50%, 70%, 85%, 100%).
    *   Safely **Close Widget**.

---

## ⚙️ Setting Up Auto-Start on Boot

The widget can be configured to start automatically when your computer turns on:
1.  Press `Win + R` on your keyboard, type **`shell:startup`**, and hit Enter.
2.  Create a shortcut to `widget.py` (or a `.bat` launcher) and place it in that startup folder.
3.  Alternatively, use the provided launcher: `Spotify Widget.bat`.

*To disable auto-start, simply delete the shortcut from that folder.*

---

## 🧠 How It Works

This widget uses the modular **PyWinRT** bindings to access the native Windows Runtime (WinRT) APIs. 

Specifically, it queries the `GlobalSystemMediaTransportControlsSessionManager` class. This is the same system-level manager that controls the Windows media overlay (shown when you press volume or media keys). Because it reads media details locally from the Windows OS session, it has **zero network overhead**, requires **no Spotify Developer client IDs/secrets**, and is completely **independent of Spotify Premium**.

---

## 🛠️ Troubleshooting

### The widget shows "Nothing Playing" when Spotify is open
1.  **Play a track**: Windows does not register an active session until a track is actively playing. Log in to Spotify and hit play.
2.  **Verify Spotify Integration**: In the Spotify Desktop client, go to Settings -> Display, and ensure **"Show desktop overlay when using media keys"** is enabled.
3.  **Test with other apps**: Play a YouTube video in Chrome or Edge. The widget should update to show the YouTube video title. If it does, the widget is working perfectly, and Spotify just needs to be playing.

---

## 📂 Project Structure

```text
SpotifyWidget/
│
├── widget.py          # Main application code (GUI & WinRT media listener)
├── config.json        # Auto-generated configuration (saves position, mode, color, opacity)
├── requirements.txt   # Python dependency list
├── .gitignore         # Git ignore rules for cached, IDE, and config files
├── README.md          # Project documentation (this file)
└── tests/             # Subfolder containing API validation tools
    ├── test_media.py      # Basic media session info retrieval script
    └── test_thumbnail.py  # Script validating cover art stream extraction
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
