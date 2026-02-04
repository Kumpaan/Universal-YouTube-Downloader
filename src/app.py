"""!
@file app.py
@brief Main application logic class.
@details Orchestrates the GUI, Multi-threading, and `yt-dlp` execution.
"""

import customtkinter as ctk
import yt_dlp
import threading
import os
import sys
import re
import requests
import time
import shutil
from PIL import Image
from io import BytesIO
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from tkinter import filedialog, messagebox

# OS Specific Imports
if os.name == 'nt':
    import ctypes

# Local Modules
from settings import *
from utils import get_bin_path, clean_filename_string
from ui_components import TrackEditorDialog


class DownloaderApp(ctk.CTk):
    """!
    @brief The primary Application Class inheriting from customtkinter.CTk.
    """

    def __init__(self):
        """!
        @brief Constructor. Initializes window, state flags, and UI.
        """
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.configure(fg_color=YT_BG)
        self.resizable(0, 0)

        # ID Setup (Windows Taskbar Grouping)
        if os.name == 'nt':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
                icon_path = get_bin_path("icon.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
            except Exception:
                pass

        # --- State Flags ---
        ## @var is_downloading
        # Boolean flag (1/0) to prevent multiple download threads.
        self.is_downloading = 0

        ## @var cancel_download
        # Boolean flag (1/0) to signal the thread to stop.
        self.cancel_download = 0

        ## @var target_folder
        # The currently selected download directory.
        self.target_folder = os.path.join(os.path.expanduser("~"), "Downloads")

        ## @var cover_art_path
        # Path to the user-selected cover art image.
        self.cover_art_path = ""

        ## @var custom_tracks
        # List of renamed strings from the Editor.
        self.custom_tracks = None

        ## @var selected_indices_str
        # String for yt-dlp --playlist-items (e.g., "1,2,5"). None implies "all".
        self.selected_indices_str = None

        self.overwrite_permission = None

        # Init UI & Checks
        self.create_widgets()
        self.check_ffmpeg_integrity()

    def create_widgets(self):
        """!
        @brief Builds the GUI elements (Buttons, Tabs, Inputs).
        """
        self.lbl_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"),
                                      text_color=TEXT_WHITE)
        self.lbl_title.pack(pady=10)

        # --- URL Input Area ---
        self.frame_url = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url.pack(pady=5)
        self.entry_url = ctk.CTkEntry(self.frame_url, placeholder_text="Paste Link Here", width=400, fg_color=YT_SEC,
                                      border_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_url.grid(row=0, column=0, padx=5)
        self.entry_url.bind("<Return>", lambda event: self.load_video_info_thread())
        self.entry_url.bind("<Control-v>", lambda event: self.after(100, self.load_video_info_thread))
        self.btn_paste = ctk.CTkButton(self.frame_url, text="Paste Link", width=80, command=self.paste_and_load,
                                       fg_color=YT_SEC, hover_color="gray")
        self.btn_paste.grid(row=0, column=1, padx=5)

        # --- Preview Area ---
        self.frame_preview = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_preview.pack(pady=5)
        self.lbl_thumbnail = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_thumbnail.grid(row=0, column=0, padx=10)
        self.lbl_cover_preview = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_cover_preview.grid(row=0, column=1, padx=10)
        self.lbl_video_title = ctk.CTkLabel(self, text="", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_video_title.pack(pady=0)

        # --- Tab View ---
        self.tab_view = ctk.CTkTabview(self, width=550, height=350, fg_color=YT_SEC, segmented_button_fg_color=YT_BG,
                                       segmented_button_selected_color=YT_RED,
                                       segmented_button_selected_hover_color=YT_RED_HOVER)
        self.tab_view.pack(pady=10)
        self.tab_std = self.tab_view.add("Standard Download")
        self.tab_album = self.tab_view.add("Music Album Maker")

        # === Standard Tab ===
        self.lbl_std_info = ctk.CTkLabel(self.tab_std, text="Standard: Auto-creates folders for Playlists.",
                                         text_color="gray")
        self.lbl_std_info.pack(pady=5)

        self.opt_format = ctk.CTkOptionMenu(self.tab_std, values=["Video (MP4)", "Audio Only (MP3)"],
                                            command=self.update_quality_options, fg_color=YT_RED, button_color=YT_RED)
        self.opt_format.pack(pady=5)

        self.opt_quality = ctk.CTkOptionMenu(self.tab_std, values=["1080p", "720p", "480p", "360p"], fg_color=YT_SEC,
                                             button_color=YT_SEC)
        self.opt_quality.pack(pady=5)

        self.check_playlist = ctk.CTkCheckBox(self.tab_std, text="Download as Playlist / Mix", onvalue=1, offvalue=0)
        self.check_playlist.select()
        self.check_playlist.pack(pady=10)

        # New: Playlist Filter Button for Standard Tab
        self.btn_std_select = ctk.CTkButton(self.tab_std, text="Select Videos / Edit Names",
                                            command=self.launch_track_editor, fg_color=YT_SEC, hover_color="gray",
                                            border_width=1, border_color="gray")
        self.btn_std_select.pack(pady=5)

        # === Album Tab ===
        self.lbl_alb_info = ctk.CTkLabel(self.tab_album, text="Album: Creates 'Artist - Album' folder.",
                                         text_color="gray")
        self.lbl_alb_info.pack(pady=2)

        self.entry_artist = ctk.CTkEntry(self.tab_album, placeholder_text="Artist Name", width=300)
        self.entry_artist.pack(pady=5)
        self.entry_album = ctk.CTkEntry(self.tab_album, placeholder_text="Album Name", width=300)
        self.entry_album.pack(pady=5)
        self.entry_year = ctk.CTkEntry(self.tab_album, placeholder_text="Year", width=300)
        self.entry_year.pack(pady=5)

        self.opt_album_quality = ctk.CTkOptionMenu(self.tab_album, values=["320kbps", "192kbps", "128kbps"],
                                                   fg_color=YT_SEC, button_color=YT_SEC)
        self.opt_album_quality.set("192kbps")
        self.opt_album_quality.pack(pady=5)

        self.frame_alb_btns = ctk.CTkFrame(self.tab_album, fg_color="transparent")
        self.frame_alb_btns.pack(pady=5)
        self.btn_cover = ctk.CTkButton(self.frame_alb_btns, text="Select Cover Art", command=self.select_cover_art,
                                       fg_color=YT_SEC, hover_color="gray", width=140)
        self.btn_cover.grid(row=0, column=0, padx=5)
        self.btn_edit_tracks = ctk.CTkButton(self.frame_alb_btns, text="Fetch & Edit Tracklist",
                                             command=self.launch_track_editor, fg_color=YT_SEC, hover_color="gray",
                                             border_width=1, border_color=YT_RED, width=140)
        self.btn_edit_tracks.grid(row=0, column=1, padx=5)

        # --- Folder Selection ---
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=5)
        self.entry_folder = ctk.CTkEntry(self.frame_folder, width=350, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_folder.insert(0, self.target_folder)
        self.entry_folder.grid(row=0, column=0, padx=5)
        self.btn_browse = ctk.CTkButton(self.frame_folder, text="Browse", width=100, command=self.browse_folder,
                                        fg_color=YT_SEC, hover_color="gray")
        self.btn_browse.grid(row=0, column=1, padx=5)

        # --- Action Buttons ---
        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.pack(pady=10)
        self.btn_download = ctk.CTkButton(self.frame_actions, text="START DOWNLOAD", command=self.start_thread,
                                          fg_color=YT_RED, hover_color=YT_RED_HOVER, width=180, height=40,
                                          font=("Arial", 14, "bold"))
        self.btn_download.grid(row=0, column=0, padx=5)
        self.btn_stop = ctk.CTkButton(self.frame_actions, text="STOP", command=self.stop_download, fg_color="gray",
                                      state="disabled", width=80, height=40, font=("Arial", 12, "bold"))
        self.btn_stop.grid(row=0, column=1, padx=5)
        self.btn_open_folder = ctk.CTkButton(self.frame_actions, text="Open Folder", command=self.open_target_folder,
                                             fg_color="transparent", border_width=1, border_color="gray",
                                             text_color="gray", width=100, height=40, state="disabled")
        self.btn_open_folder.grid(row=0, column=2, padx=5)

        # --- Status Bar ---
        self.progress_bar = ctk.CTkProgressBar(self, width=500, progress_color=YT_RED)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Arial", 14))
        self.lbl_status.pack(pady=5)
        self.lbl_detail_status = ctk.CTkLabel(self, text="", text_color="gray", font=("Arial", 11))
        self.lbl_detail_status.pack(pady=2)

    # --- Logic ---

    def check_ffmpeg_integrity(self):
        """!
        @brief Verifies existence of FFmpeg binary on startup.
        @details Disables the download button if FFmpeg is missing.
        """
        if os.name == 'nt':
            if not os.path.exists(get_bin_path("ffmpeg.exe")):
                self.lbl_status.configure(text="CRITICAL ERROR: bin/ffmpeg.exe missing!", text_color="red")
                self.btn_download.configure(state="disabled")
        else:
            if not shutil.which("ffmpeg"):
                self.lbl_status.configure(text="CRITICAL ERROR: ffmpeg not found!", text_color="red")
                self.btn_download.configure(state="disabled")

    def stop_download(self):
        """!
        @brief Signals the download thread to stop gracefully.
        """
        if self.is_downloading:
            self.cancel_download = 1
            self.lbl_status.configure(text="Stopping...", text_color="yellow")
            self.btn_stop.configure(state="disabled")

    def update_quality_options(self, choice):
        """!
        @brief Updates the Quality dropdown options based on Format selection.
        @param choice The selected string ("Video" or "Audio").
        """
        if choice == "Video (MP4)":
            self.opt_quality.configure(values=["1080p", "720p", "480p", "360p"])
            self.opt_quality.set("1080p")
        else:
            self.opt_quality.configure(values=["320kbps", "192kbps", "128kbps"])
            self.opt_quality.set("192kbps")

    def browse_folder(self):
        """!
        @brief Opens a native OS dialog to select destination folder.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder = folder
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, self.target_folder)

    def select_cover_art(self):
        """!
        @brief Opens a dialog to select a JPG/PNG image for album art.
        """
        img_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if img_path:
            self.cover_art_path = img_path
            try:
                pil_image = Image.open(img_path)
                pil_image = pil_image.resize((150, 150))
                tk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
                self.lbl_cover_preview.configure(image=tk_image, text="")
                self.lbl_status.configure(text="Cover Art Selected", text_color="green")
            except:
                self.lbl_status.configure(text="Invalid Image", text_color="red")

    def open_target_folder(self):
        """!
        @brief Opens the destination folder in the OS File Explorer.
        """
        if hasattr(self, 'final_download_path') and os.path.exists(self.final_download_path):
            path = self.final_download_path
        else:
            path = self.entry_folder.get()

        if os.path.exists(path):
            if os.name == 'nt':
                os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])

    def paste_and_load(self):
        """!
        @brief Pastes content from clipboard and triggers info fetch.
        """
        try:
            content = self.clipboard_get()
            if "import " in content or "def " in content:
                messagebox.showerror("Error", "You pasted Python code, not a URL!")
                return
            self.entry_url.delete(0, "end")
            self.entry_url.insert(0, content)
            self.load_video_info_thread()
        except:
            self.lbl_status.configure(text="Clipboard Empty", text_color="red")

    def load_video_info_thread(self):
        """!
        @brief Spawns a background thread to fetch video metadata/thumbnail.
        """
        url = self.entry_url.get()
        if url: threading.Thread(target=self.fetch_thumbnail, args=(url,), daemon=True).start()

    def fetch_thumbnail(self, url):
        """!
        @brief Logic to fetch video title and thumbnail using yt-dlp.
        @param url The YouTube URL.
        """
        try:
            self.lbl_status.configure(text="Fetching Info...", text_color="yellow")
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist'}) as ydl:
                info = ydl.extract_info(url, download=False)

            thumb_url = None
            title = info.get('title', 'Unknown')

            # Smart thumbnail finder logic
            if info.get('_type') == 'playlist':
                if info.get('thumbnails'):
                    thumb_url = info['thumbnails'][-1]['url']
                elif info.get('thumbnail'):
                    thumb_url = info['thumbnail']
                if not thumb_url and 'entries' in info:
                    entries = list(info['entries'])
                    if len(entries) > 0:
                        first = entries[0]
                        thumb_url = first.get('thumbnail')
                        if not thumb_url:
                            # Fallback scan single video
                            try:
                                vid_url = first.get('url') or f"https://www.youtube.com/watch?v={first.get('id')}"
                                with yt_dlp.YoutubeDL({'quiet': True}) as ydl_s:
                                    s_info = ydl_s.extract_info(vid_url, download=False)
                                    thumb_url = s_info.get('thumbnail')
                            except:
                                pass
            else:
                thumb_url = info.get('thumbnail')

            if thumb_url:
                response = requests.get(thumb_url)
                pil_image = Image.open(BytesIO(response.content)).resize((250, 140))
                tk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(250, 140))
                self.lbl_thumbnail.configure(image=tk_image, text="")

            self.lbl_video_title.configure(text=title[:50])
            self.lbl_status.configure(text="Ready", text_color="gray")
        except:
            self.lbl_status.configure(text="Could not load preview", text_color="red")

    def launch_track_editor(self):
        """!
        @brief Opens the Track Editor popup. Fetches list if needed.
        """
        url = self.entry_url.get()
        if not url: return

        # Determine which button triggered this to update text state
        active_btn = self.btn_edit_tracks if self.tab_view.get() == "Music Album Maker" else self.btn_std_select

        active_btn.configure(state="disabled", text="Fetching...")
        threading.Thread(target=self.fetch_tracks_for_editor, args=(url, active_btn), daemon=True).start()

    def fetch_tracks_for_editor(self, url, btn_widget):
        """!
        @brief Background thread to get playlist entries for editing.
        @param url The Playlist/Video URL.
        @param btn_widget The button widget to re-enable after fetching.
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            tracks = [entry.get('title') for entry in info['entries']] if 'entries' in info else [info.get('title')]
            self.after(0, lambda: TrackEditorDialog(self, tracks, self.save_tracklist))
        except:
            self.lbl_status.configure(text="Error fetching tracklist", text_color="red")

        btn_widget.configure(state="normal", text="Select Videos / Edit Names")

    def save_tracklist(self, new_titles, download_states):
        """!
        @brief Callback from TrackEditorDialog. Stores user choices.

        @param new_titles List of strings (renamed titles).
        @param download_states List of integers (1/0) indicating check state.
        """
        self.custom_tracks = new_titles

        # Calculate indices string for yt-dlp (e.g., "1,2,5")
        # yt-dlp playlist indices are 1-based.
        selected_indices = []
        count = 0
        for i, state in enumerate(download_states):
            if state == 1:
                selected_indices.append(str(i + 1))
                count += 1

        if len(selected_indices) == len(download_states):
            self.selected_indices_str = None  # Download All
        else:
            self.selected_indices_str = ",".join(selected_indices)

        self.lbl_status.configure(text=f"Selected {count} of {len(download_states)} tracks.", text_color="green")

    def start_thread(self):
        """!
        @brief Validates inputs and starts the main download thread.
        """
        if self.is_downloading == 1: return
        self.cancel_download = 0
        self.btn_open_folder.configure(state="disabled", text_color="gray")
        self.overwrite_permission = None

        url = self.entry_url.get()
        base_folder = self.entry_folder.get()
        if not url: return

        if not os.path.exists(base_folder):
            try:
                os.makedirs(base_folder)
            except:
                self.lbl_status.configure(text="Invalid Folder", text_color="red")
                return

        self.is_downloading = 1
        self.btn_download.configure(state="disabled", text="Running...")
        self.btn_stop.configure(state="normal", fg_color="red")

        threading.Thread(target=self.pre_download_logic, args=(url, base_folder), daemon=True).start()

    def trigger_ask_overwrite(self, folder_name):
        """!
        @brief Pop-up asking user to confirm merging into an existing folder.
        """
        res = messagebox.askyesno("Folder Exists", f"Folder '{folder_name}' exists.\nMerge/Overwrite?")
        self.overwrite_permission = res

    def pre_download_logic(self, url, base_folder):
        """!
        @brief Determines destination paths and handles playlist folder creation logic.
        """
        try:
            current_tab = self.tab_view.get()
            final_path = base_folder
            self.lbl_status.configure(text="Checking Paths...", text_color="yellow")

            if current_tab == "Music Album Maker":
                artist = self.entry_artist.get().strip()
                album = self.entry_album.get().strip()
                if not artist or not album:
                    self.lbl_status.configure(text="Error: Artist & Album Required", text_color="red")
                    self.finish_download(0)
                    return
                final_path = os.path.join(base_folder, f"{artist} - {album}")
            else:
                # Standard Tab Logic
                is_playlist = self.check_playlist.get()
                if "list=" in url and is_playlist == 1:
                    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist'}) as ydl:
                        info = ydl.extract_info(url, download=False, process=False)
                        if info.get('_type') == 'playlist':
                            title = "".join(
                                [c for c in info.get('title', 'Playlist') if c.isalnum() or c == ' ']).strip()
                            final_path = os.path.join(base_folder, title)

            if final_path != base_folder and os.path.exists(final_path):
                self.after(0, lambda: self.trigger_ask_overwrite(os.path.basename(final_path)))
                while self.overwrite_permission is None:
                    if self.cancel_download: return
                    time.sleep(0.1)
                if self.overwrite_permission is False:
                    self.lbl_status.configure(text="Download Cancelled", text_color="yellow")
                    self.finish_download(0)
                    return

            self.final_download_path = final_path
            self.run_download(url, final_path)

        except Exception as e:
            print(f"Pre-download error: {e}")
            self.finish_download(0)

    def run_download(self, url, folder_path):
        """!
        @brief Configures `yt-dlp` options and executes the download.
        @param url Source URL.
        @param folder_path Output directory.
        """
        try:
            self.lbl_status.configure(text="Starting...", text_color=TEXT_WHITE)
            current_tab = self.tab_view.get()

            ffmpeg_dir = os.path.dirname(get_bin_path("ffmpeg.exe"))

            ydl_opts = {
                'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
                'progress_hooks': [self.progress_hook],
                'ignoreerrors': False,
                'verbose': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
            }

            # Apply Filter if selected
            if self.selected_indices_str:
                ydl_opts['playlist_items'] = self.selected_indices_str

            if os.name == 'nt': ydl_opts['ffmpeg_location'] = ffmpeg_dir

            if current_tab == "Standard Download":
                fmt = self.opt_format.get()
                quality = self.opt_quality.get()

                if self.check_playlist.get() == 0:
                    ydl_opts['noplaylist'] = True
                else:
                    if "list=" in url and not self.selected_indices_str:
                        # Only cap infinite lists if user hasn't manually selected items
                        ydl_opts['playlistend'] = 100
                    if "list=" in url:
                        ydl_opts['outtmpl'] = f'{folder_path}/%(title)s.%(ext)s'

                if fmt == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                                                   'preferredquality': quality.replace("kbps", "")}]
                else:
                    height = quality.replace("p", "")
                    ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

            elif current_tab == "Music Album Maker":
                ydl_opts['outtmpl'] = f'{folder_path}/%(playlist_index)s-%(title)s.%(ext)s'
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                                               'preferredquality': self.opt_album_quality.get().replace("kbps", "")}]
                if not self.selected_indices_str:
                    ydl_opts['playlistend'] = 100

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.finish_download(1)
        except Exception as e:
            if "User Cancelled" in str(e):
                self.lbl_status.configure(text="Cancelled", text_color="yellow")
            else:
                print(f"Error: {e}")
                self.lbl_status.configure(text="Error: See Console", text_color="red")
            self.finish_download(0)

    def progress_hook(self, d):
        """!
        @brief Callback for yt-dlp to update UI progress bar.
        """
        if self.cancel_download == 1: raise Exception("User Cancelled")
        if d['status'] == 'downloading':
            try:
                p = float(d.get('_percent_str', '0%').replace('%', '')) / 100
                self.progress_bar.set(p)
                self.lbl_status.configure(text=f"Downloading: {d.get('info_dict', {}).get('title', 'Unknown')[:30]}...")
                self.lbl_detail_status.configure(text=f"Speed: {d.get('_speed_str')} | ETA: {d.get('_eta_str')}")
            except:
                pass
        elif d['status'] == 'finished':
            self.lbl_status.configure(text="Processing...", text_color="yellow")

    def finish_download(self, success):
        """!
        @brief Post-download cleanup and UI reset.
        """
        self.is_downloading = 0
        self.btn_download.configure(state="normal", text="START DOWNLOAD")
        self.btn_stop.configure(state="disabled", fg_color="gray")
        self.progress_bar.set(0)

        # Clear filters for next run
        self.selected_indices_str = None

        if success == 1:
            self.lbl_status.configure(text="Complete!", text_color="green")
            self.lbl_detail_status.configure(text="Files saved.")
            self.btn_open_folder.configure(state="normal", text_color=TEXT_WHITE, border_color=YT_RED)
            if self.tab_view.get() == "Music Album Maker": self.batch_tag_files()

    def batch_tag_files(self):
        """!
        @brief Scans output folder to tag MP3s (Album Mode only).
        @details Uses 'mutagen' to set ID3 tags and embed cover art.
        """
        artist = self.entry_artist.get()
        album = self.entry_album.get()
        year = self.entry_year.get()
        folder = self.final_download_path
        self.lbl_status.configure(text="Tagging...", text_color="yellow")

        for filename in os.listdir(folder):
            if filename.endswith(".mp3"):
                try:
                    filepath = os.path.join(folder, filename)

                    # Logic to find which playlist index this file corresponds to
                    # Filename format from yt-dlp: "01-Title.mp3"
                    file_index = None
                    track_prefix = ""
                    match = re.match(r'^(\d+)-', filename)
                    if match:
                        track_prefix = match.group(1)
                        file_index = int(track_prefix) - 1

                    # Look up custom name from list if available
                    # NOTE: custom_tracks contains ALL titles (checked and unchecked).
                    # Since yt-dlp preserves the original playlist index in %(playlist_index)s,
                    # we can map directly to the custom_tracks list index.
                    if self.custom_tracks and file_index is not None and 0 <= file_index < len(self.custom_tracks):
                        clean_name = self.custom_tracks[file_index]
                    else:
                        clean_name = clean_filename_string(os.path.splitext(filename)[0], artist)

                    if not re.match(r'^\d-', clean_name) and track_prefix:
                        clean_name = f"{track_prefix}-{clean_name}"

                    # Tagging
                    try:
                        audio = EasyID3(filepath)
                    except:
                        audio = EasyID3()
                        audio.save(filepath)
                        audio = EasyID3(filepath)

                    if artist: audio['artist'] = artist
                    if album: audio['album'] = album
                    if year: audio['date'] = year
                    if track_prefix: audio['tracknumber'] = track_prefix
                    audio['title'] = re.sub(r'^\d+-', '', clean_name)
                    audio.save()

                    if self.cover_art_path and os.path.exists(self.cover_art_path):
                        audio_id3 = ID3(filepath)
                        with open(self.cover_art_path, 'rb') as art:
                            audio_id3.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=art.read()))
                        audio_id3.save()

                    new_path = os.path.join(folder, f"{clean_name}.mp3")
                    if not os.path.exists(new_path): os.rename(filepath, new_path)
                except Exception as e:
                    print(f"Tag Error: {e}")

        self.custom_tracks = None
        self.lbl_status.configure(text="Album Complete!", text_color="green")