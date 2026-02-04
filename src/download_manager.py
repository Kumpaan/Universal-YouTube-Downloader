"""!
@file download_manager.py
@brief Wrapper for yt-dlp execution.
@details Handles configuration generation and execution of downloads.
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
                # Remove special chars to make it folder-safe
                return "".join([c for c in title if c.isalnum() or c==' ']).strip()
    except:
        return None
    return None

def run_downloader(config, progress_callback):
    """!
    @brief Configures and runs yt-dlp.

    @param config Dictionary containing all options (url, folder, format, etc).
    @param progress_callback Function to handle yt-dlp progress hooks.
    @throws Exception if download fails or is cancelled.
    """

    url = config['url']
    folder_path = config['folder']

    # Locate FFmpeg
    ffmpeg_dir = os.path.dirname(get_bin_path("ffmpeg.exe"))

    # Base Options
    ydl_opts = {
        'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
        'progress_hooks': [progress_callback],
        'ignoreerrors': False,
        'verbose': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    }

    # OS Specific FFmpeg location
    if os.name == 'nt':
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    # Apply Selective Download
    if config.get('selected_indices'):
        ydl_opts['playlist_items'] = config['selected_indices']

    # --- Mode Configuration ---

    if config['mode'] == "standard":
        # Standard Mode Logic

        # If the App didn't detect a valid playlist, force single video mode.
        # This handles cases where user pastes a mix link or single video.
        if not config['detected_playlist']:
            ydl_opts['noplaylist'] = True
        else:
            # It IS a valid playlist
            if "list=" in url:
                ydl_opts['outtmpl'] = f'{folder_path}/%(title)s.%(ext)s'
                # Safety Cap: If user downloaded "whole playlist" without selecting specific items, cap at 100
                if not config.get('selected_indices'):
                    ydl_opts['playlistend'] = 100

        # Quality / Format Logic
        if config['format_type'] == "audio":
            ydl_opts['format'] = 'bestaudio/best'
            kbps = config['quality'].replace("kbps", "")
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': kbps
            }]
        else:
            # Video
            height = config['quality'].replace("p", "")
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

    elif config['mode'] == "album":
        # Album Mode Logic
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