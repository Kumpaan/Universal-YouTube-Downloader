# Universal YouTube Downloader (v0.3.0)

A professional desktop application for downloading YouTube videos and playlists. It features a specific "Album Maker" mode that converts playlists into properly tagged, organized music albums with cover art.

**New in v0.3.0:** Selective downloading, real-time playlist progress tracking, and a completely refactored codebase for stability.

## 1. Installation (For Users)

This application is distributed as a portable executable. It does not require a system installation, but it relies on external dependencies.

### Prerequisites
* **Windows 10 or 11 (Linux supported via source)**
* **FFmpeg:** This software **will not work** without FFmpeg. It is required for converting audio and merging high-quality video streams.

### Setup Steps
1. Download the release `.zip` file.
2. **Extract** the zip file to a folder. Do not run it directly from inside the zip.
3. Ensure the folder contains:
    * `YouTubeDownloader_v0.3.0.exe`
    * `bin/` (Folder)
4. Ensure the `bin/` folder contains these files side by side:
    * `ffmpeg.exe`
    * `ffprobe.exe`
    * `icon.ico`
5. Run the executable.

### Troubleshooting Startup
* **Antivirus Warning:** Windows Defender may flag this app because it is not digitally signed (which is expensive). You may need to select "More Info" -> "Run Anyway".
* **Missing FFmpeg:** If the "Start Download" button is disabled (Gray), the app cannot find FFmpeg. Check the status text at the bottom—it will tell you exactly what is missing.

---

## 2. Features

* **Dark Mode UI:** Styled to match the YouTube dark theme.
* **Smart Clipboard:** Automatically detects links in the clipboard and fetches thumbnail previews.
* **Dual Modes:**
    * **Standard:** Downloads Video (MP4) or Audio (MP3).
    * **Album Maker:** Specialized mode for music organization (Auto-Tagging, Cover Art).
* **Selective Downloading:** (New!) Uncheck specific videos in a playlist to skip them.
* **Live Progress Tracking:**
    * **File Progress:** Real-time speed, size, and ETA for the current file.
    * **Playlist Progress:** Accurate counter (e.g., "Video 3 of 10") that respects your selection.
* **Safety Features:**
    * **Mix Blocker:** Prevents crashing by blocking infinite "YouTube Mix" URLs.
    * **Quality Enforcer:** Strict checks ensure you get 1080p; the app will error out rather than silently giving you low-quality 360p.
    * **Overwrite Protection:** Asks for confirmation before overwriting existing files.

---

## 3. How to Use

### Mode A: Standard Download
Use this for casual downloading or archiving.

1.  **Paste Link:** Use the "Paste" button.
2.  **Playlist Detection:**
    * If you paste a **Single Video**, the "Select Videos" button is disabled.
    * If you paste a **Playlist**, the button becomes active.
3.  **Select Videos (Optional):** Click the button to see the tracklist. Uncheck any videos you don't want.
4.  **Select Format:** Choose "Video (MP4)" or "Audio Only (MP3)".
5.  **Download:** Click "START DOWNLOAD". The files will be saved in your chosen folder (sub-foldered by Playlist name).

### Mode B: Music Album Maker
Turn a YouTube Playlist into a clean MP3 album.

1.  **Input:** Paste a Playlist link.
2.  **Tags:** Fill in **Artist**, **Album**, and **Year**.
3.  **Cover Art:** Click "Select Cover Art" to embed a JPG/PNG into every file.
4.  **Download:** Click "START DOWNLOAD".
5.  **The Process:**
    * Downloads audio -> Converts to MP3 -> Renames to `Song Name.mp3` -> Embeds ID3 Tags & Cover Art -> Saves to `Artist - Album/`.

---

## 4. Development (For Programmers)

The project uses a Model-View-Controller (MVC) structure for maintainability.

### Requirements
* Python 3.10+
* FFmpeg (in `./bin/` or global PATH)

### Setup
1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install customtkinter yt-dlp mutagen pillow requests pyinstaller
    ```

### File Structure
* `main.py`: Entry point.
* `app.py`: The glue connecting View and Logic.
* `view.py`: All GUI widgets and layout code.
* `logic.py`: All business logic, threading, and event handling.
* `download_manager.py`: Wrapper for `yt-dlp`.
* `tag_manager.py`: Wrapper for `mutagen` (Tagging).
* `utils.py`: Helper paths and string cleaning.
* `settings.py`: Constants and config.

### Building the Executable
Run this command from the project root:
```bash
pyinstaller --noconsole --onefile --name YouTubeDownloader_v0.3.0 --collect-all customtkinter main.py
```

*Note: After building, you must manually create a `bin` folder next to the `.exe` and place `ffmpeg.exe`, `ffprobe.exe`, and `icon.ico` inside it.*

## 5. Disclaimer
Downloading copyrighted content from YouTube may violate their Terms of Service. This tool is provided for educational and personal archiving purposes only. Use responsibly.