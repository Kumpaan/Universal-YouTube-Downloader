import os
import sys
import re


def get_bin_path(filename):
    """
    Returns the path to a binary file.
    Checks inside './bin/' first, then checking the root folder.
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
    """ Get absolute path to resource (for PyInstaller) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def clean_filename_string(raw_title, artist_name):
    """
    Pure logic to clean a filename string.
    Removes artist name redundancy and junk keywords.
    """
    clean = raw_title

    # Remove Artist Name redundancy
    if artist_name and clean.lower().startswith(artist_name.lower()):
        clean = clean[len(artist_name):]
        clean = re.sub(r'^[\s\-\:]+', '', clean)

    # Remove Junk in brackets
    clean = re.sub(r'\s*[\(\[].*?(official|video|lyrics|4k|hd|hq|visualizer).*?[\)\]]', '', clean, flags=re.IGNORECASE)

    return clean.strip()