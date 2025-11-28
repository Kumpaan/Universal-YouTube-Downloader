# Universal YouTube Downloader (v0.2.0)

A desktop application for downloading YouTube videos and playlists. It features a specific "Album Maker" mode that converts playlists into properly tagged, organized music albums with cover art.

## 1. Installation (For Users)

This application is distributed as a portable executable. It does not require a system installation, but it relies on external dependencies.

### Prerequisites
* **Windows 10 or 11**
* **FFmpeg:** This software **will not work** without FFmpeg. It is required for converting audio and merging video streams.

### Setup Steps
1. [Download](https://github.com/Kumpaan/Universal-YouTube-Downloader/releases/download/v0.1.0/YouTubeDownloader_v0.1.0.zip) the release `.zip` file.
1.1. If the download is slow download it from [Google Drive](https://drive.google.com/file/d/1U_dgmNFuNpINMYAF5n-1M2Pe3G7fzsU3/view?usp=sharing)
2. **Extract** the zip file to a folder. Do not run it directly from inside the zip.
3. Ensure the folder contains this file and folder:
    * `downloader.exe`
    * `bin`
4. Ensure the bin folder contains these files side by side:
    * `ffmpeg.exe`
    * `ffprobe.exe`
    * `icon.con`
5. Run `downloader.exe`.

### Troubleshooting Startup
* **Antivirus Warning:** Because this application is not digitally signed (which costs money), Windows Defender or SmartScreen may flag it. You will likely need to select "More Info" -> "Run Anyway" or whitelist the folder.
* **Missing FFmpeg:** If the app launches but the "Start Download" button is disabled, check the status text at the bottom. It will tell you if `ffmpeg.exe` is missing from the directory.

---

## 2. Features

* **Dark Mode UI:** Styled to match the YouTube dark theme.
* **Auto-Paste & Load:** Automatically detects links in the clipboard and fetches thumbnail previews.
* **Dual Modes:**
    * **Standard:** Downloads Video (MP4) or Audio (MP3). Auto-downloads full playlists if a playlist link is provided.
    * **Album Maker:** Specialized mode for music organization.
* **Metadata Editing:** Automatically cleans "dirty" YouTube titles (removes "Official Video", "Lyrics", etc.).
* **Playlist Track Editor:** (New in v0.2.0) Fetch tracklists and manually rename songs before downloading.
* **Custom Icon:** The app now features a dedicated icon.
* **Cover Art:** Embeds custom JPG/PNG images into MP3 files.
* **Smart Folder Management:**
    * Standard playlists create their own subfolders.
    * Albums create `Artist - Album` folders.
    * Checks for existing files to prevent accidental overwrites.

---

## 3. How to Use

### Mode A: Standard Download
Use this for casual downloading of single videos or archiving entire playlists as-is.

1.  **Paste Link:** Use the "Paste Link" button or press `Ctrl+V`.
2.  **Select Format:** Choose "Video (MP4)" or "Audio Only (MP3)".
3.  **Select Quality:**
    * Video: 1080p, 720p, etc.
    * Audio: 320kbps, 192kbps, etc.
4.  **Download:** Click "START DOWNLOAD".
5.  **Result:** Files are saved to your Downloads folder (or selected path).

### Mode B: Music Album Maker
Use this to turn a YouTube Playlist into a clean MP3 album.

1.  **Input:** Paste a link to a **Playlist** (not a single video).
2.  **Tags:** Fill in **Artist**, **Album**, and **Year**. These are required.
3.  **Cover Art:** Click "Select Cover Art" and choose a square JPG/PNG.
4.  **Edit Tracks (Optional):** Click "Fetch & Edit Tracklist" to review and rename songs before downloading.
4.  **Download:** Click "START DOWNLOAD".
5.  **The Process:**
    * The app downloads the audio.
    * It converts it to MP3.
    * It renames the file to `01-SongName.mp3` (based on playlist order).
    * It embeds the Cover Art and ID3 tags.
    * It saves everything into a folder named `Artist - Album`.

---

## 4. Development (For Programmers)

If you want to modify the source code, follow these steps.

### Requirements
* Python 3.10+
* FFmpeg installed globally or placed in the project root.

### Setup
1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install customtkinter yt-dlp mutagen pillow requests pyinstaller
    ```

### Building the Exe
To compile the application yourself:
```bash
pyinstaller --noconsole --onefile --collect-all customtkinter downloader.py
```

## 5. Disclaimer
Downloading copyrighted content from YouTube may violate their Terms of Service. This tool is provided for educational and personal archiving purposes only. Use responsibly.
