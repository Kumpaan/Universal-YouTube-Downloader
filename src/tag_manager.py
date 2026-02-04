"""!
@file tag_manager.py
@brief Logic for post-processing audio files.
@details Handles ID3 tagging, file renaming, and cover art embedding.
"""

import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from utils import clean_filename_string


def process_album_tags(folder_path, metadata, custom_tracks, status_callback):
    """!
    @brief Scans a folder and applies Album tags to all MP3 files.

    @param folder_path Absolute path to the folder containing MP3s.
    @param metadata Dictionary containing 'artist', 'album', 'year', 'cover_path'.
    @param custom_tracks List of renamed titles (optional).
    @param status_callback Function to send status text updates to the GUI.
    """
    status_callback("Tagging & Renaming...")

    artist = metadata.get('artist')
    album = metadata.get('album')
    year = metadata.get('year')
    cover_path = metadata.get('cover_path')

    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            try:
                filepath = os.path.join(folder_path, filename)

                # 1. Determine Track Index and Name
                # yt-dlp saves files as "01-Title.mp3". We parse this prefix.
                file_index = None
                track_prefix = ""
                match = re.match(r'^(\d+)-', filename)
                if match:
                    track_prefix = match.group(1)
                    file_index = int(track_prefix) - 1

                # 2. Determine Clean Title
                # Check if user manually renamed this track in the Editor
                if custom_tracks and file_index is not None and 0 <= file_index < len(custom_tracks):
                    clean_name = custom_tracks[file_index]
                else:
                    # Auto-clean using regex
                    clean_name = clean_filename_string(os.path.splitext(filename)[0], artist)

                # Re-attach prefix if needed for filename sorting
                if not re.match(r'^\d-', clean_name) and track_prefix:
                    clean_name = f"{track_prefix}-{clean_name}"

                # 3. Apply ID3 Tags
                try:
                    audio = EasyID3(filepath)
                except:
                    # Create empty tags if missing
                    audio = EasyID3()
                    audio.save(filepath)
                    audio = EasyID3(filepath)

                if artist: audio['artist'] = artist
                if album: audio['album'] = album
                if year: audio['date'] = year
                if track_prefix: audio['tracknumber'] = track_prefix

                # Title tag should NOT have the "01-" prefix
                audio['title'] = re.sub(r'^\d+-', '', clean_name)
                audio.save()

                # 4. Embed Cover Art
                if cover_path and os.path.exists(cover_path):
                    audio_id3 = ID3(filepath)
                    with open(cover_path, 'rb') as art:
                        audio_id3.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=art.read()))
                    audio_id3.save()

                # 5. Rename File on Disk
                new_path = os.path.join(folder_path, f"{clean_name}.mp3")
                if not os.path.exists(new_path):
                    os.rename(filepath, new_path)

            except Exception as e:
                print(f"Tag Error on {filename}: {e}")

    status_callback("Album Complete!")