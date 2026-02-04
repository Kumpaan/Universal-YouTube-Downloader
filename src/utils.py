"""!
@file utils.py
@brief Helper utility functions.
@details Contains static logic for file path handling and string sanitization.
"""

import os
import sys
import re


def get_bin_path(filename):
    """!
    @brief Resolves the absolute path to a binary file.

    @details logic checks for the file in a `./bin/` subdirectory first (clean structure),
    then falls back to the root directory (user convenience).
    Handles Frozen (PyInstaller) and Dev environments.

    @param filename The name of the file to locate (e.g., "ffmpeg.exe").
    @return Absolute path string to the file.
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 1. Check inside /bin/ (Clean structure)
    bin_path = os.path.join(base_path, "bin", filename)
    if os.path.exists(bin_path):
        return bin_path

    # 2. Check inside Root (User convenience)
    root_path = os.path.join(base_path, filename)
    if os.path.exists(root_path):
        return root_path

    return bin_path


def resource_path(relative_path):
    """!
    @brief Resolves resource paths for PyInstaller bundling.
    @param relative_path The relative path to the asset.
    @return The absolute path to the unpacked resource in `_MEIPASS`.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def clean_filename_string(raw_title, artist_name):
    """!
    @brief Sanitizes a video title for use as a filename.

    @details Removes redundancy (Artist Name repeated in title) and junk keywords
    often found in YouTube titles (e.g., "Official Video", "Lyrics").

    @param raw_title The original video title from YouTube.
    @param artist_name The artist name entered by the user (used for redundancy check).
    @return A cleaned string ready for file system usage.
    """
    clean = raw_title

    # Remove Artist Name redundancy
    if artist_name and clean.lower().startswith(artist_name.lower()):
        clean = clean[len(artist_name):]
        clean = re.sub(r'^[\s\-\:]+', '', clean)

    # Remove Junk in brackets
    clean = re.sub(r'\s*[\(\[].*?(official|video|lyrics|4k|hd|hq|visualizer).*?[\)\]]', '', clean, flags=re.IGNORECASE)

    return clean.strip()