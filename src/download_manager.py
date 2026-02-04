"""!
@file download_manager.py
@brief Wrapper for yt-dlp execution.
@details Handles configuration generation and execution of downloads.
         Now enforces strict quality control (No 360p fallbacks).
"""

import yt_dlp
import os
from utils import get_bin_path

def fetch_playlist_title(url):
    """!
    @brief Extracts the title of a playlist without downloading it.
    @return Cleaned title string or None.
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist'}) as ydl:
            info = ydl.extract_info(url, download=False, process=False)
            if info.get('_type') == 'playlist':
                title = info.get('title', 'Playlist')
                return "".join([c for c in title if c.isalnum() or c==' ']).strip()
    except:
        return None
    return None

def run_downloader(config, progress_callback):
    """!
    @brief Configures and runs yt-dlp with strict quality enforcement.

    @param config Dictionary containing all options.
    @param progress_callback Function to handle yt-dlp progress hooks.
    """

    url = config['url']
    folder_path = config['folder']

    # 1. SETUP FFMPEG
    ffmpeg_exe = get_bin_path("ffmpeg.exe")
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)

    # Base Options
    ydl_opts = {
        'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
        'progress_hooks': [progress_callback],
        'ignoreerrors': False,
        'verbose': True,
        # REMOVED: 'extractor_args' causing the crash due to PO Token requirements
    }

    # Windows: Force yt-dlp to use our local FFmpeg
    if os.name == 'nt':
        if not os.path.exists(ffmpeg_exe):
            raise Exception(f"FFmpeg binary not found at: {ffmpeg_exe}")
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    # Apply Selective Download
    if config.get('selected_indices'):
        ydl_opts['playlist_items'] = config['selected_indices']

    # --- Mode Configuration ---
    if config['mode'] == "standard":
        # Playlist Logic
        if not config['detected_playlist']:
            ydl_opts['noplaylist'] = True
        else:
            if "list=" in url:
                ydl_opts['outtmpl'] = f'{folder_path}/%(title)s.%(ext)s'
                if not config.get('selected_indices'):
                    ydl_opts['playlistend'] = 100

        # --- QUALITY LOGIC (STRICT) ---
        if config['format_type'] == "audio":
            ydl_opts['format'] = 'bestaudio/best'
            kbps = config['quality'].replace("kbps", "")
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': kbps
            }]
        else:
            # VIDEO MODE
            # Forces separate streams (1080p video + audio) to ensure high quality
            height = config['quality'].replace("p", "")
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio'

            # Ensure it merges into MP4
            ydl_opts['merge_output_format'] = 'mp4'

    elif config['mode'] == "album":
        ydl_opts['outtmpl'] = f'{folder_path}/%(playlist_index)s-%(title)s.%(ext)s'
        ydl_opts['format'] = 'bestaudio/best'
        kbps = config['quality'].replace("kbps", "")
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': kbps
        }]

        if not config.get('selected_indices'):
            ydl_opts['playlistend'] = 100

    # Execute
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])