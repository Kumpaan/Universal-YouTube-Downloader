"""!
@file logic.py
@brief Business logic controller.
@details Handles event processing, threading, and data management.
         Separated from GUI to allow easier maintenance.
"""

import threading
import os
import shutil
import requests
import yt_dlp
from PIL import Image
from io import BytesIO
from tkinter import filedialog, messagebox

# Local Modules
from settings import *
from utils import get_bin_path
from ui_components import TrackEditorDialog
import download_manager
import tag_manager

class DownloaderLogic:
    """!
    @brief Controller class that manipulates the View.
    """

    def __init__(self, view):
        """!
        @brief Initialize Logic with a reference to the View.
        @param view Instance of DownloaderView.
        """
        self.view = view

        # State Variables
        self.is_downloading = 0
        self.cancel_download = 0
        self.target_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.cover_art_path = ""
        self.custom_tracks = None
        self.selected_indices_str = None
        self.selected_count = None
        self.overwrite_permission = None
        self.detected_playlist_mode = False

        # Internal Counter State (Fixes "Video 21 of 16" bug)
        self.internal_download_count = 0
        self.current_file_id = None

        # Dynamic Labels
        self.active_item_label = "File"
        self.active_progress_prefix = "Progress"

        # Initialize Default Values in View
        self.view.entry_folder.insert(0, self.target_folder)

        # Perform Startup Checks
        self.check_ffmpeg_integrity(self)

    # --- SETUP & CHECKS ---

    def check_ffmpeg_integrity(self, _=None):
        """! @brief Verifies FFmpeg availability and updates View status. """
        if os.name == 'nt':
            if not os.path.exists(get_bin_path("ffmpeg.exe")):
                self.view.lbl_status.configure(text="Error: bin/ffmpeg.exe missing!", text_color="red")
                self.view.btn_download.configure(state="disabled")
        else:
            if not shutil.which("ffmpeg"):
                self.view.lbl_status.configure(text="Error: ffmpeg missing!", text_color="red")
                self.view.btn_download.configure(state="disabled")

    def update_quality_options(self, choice):
        """! @brief Updates dropdown options in View based on Format selection. """
        if choice == "Video (MP4)":
            self.view.opt_quality.configure(values=["1080p", "720p", "480p", "360p"])
            self.view.opt_quality.set("1080p")
        else:
            self.view.opt_quality.configure(values=["320kbps", "192kbps", "128kbps"])
            self.view.opt_quality.set("192kbps")

    # --- FILE & FOLDER ACTIONS ---

    def browse_folder(self):
        """! @brief Opens OS dialog to select download folder. """
        f = filedialog.askdirectory()
        if f:
            self.target_folder = f
            self.view.entry_folder.delete(0, "end")
            self.view.entry_folder.insert(0, f)

    def select_cover_art(self):
        """! @brief Opens OS dialog to select cover art. """
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
        if f: self.cover_art_path = f

    def open_target_folder(self):
        """! @brief Opens the final download folder in OS Explorer. """
        path = getattr(self, 'final_download_path', self.view.entry_folder.get())
        if os.path.exists(path):
            if os.name == 'nt': os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])

    # --- THUMBNAIL & INFO FETCHING ---

    def paste_and_load(self):
        """! @brief Pastes clipboard content and triggers fetch. """
        try:
            self.view.entry_url.delete(0, "end")
            self.view.entry_url.insert(0, self.view.clipboard_get())
            self.load_video_info_thread()
        except: pass

    def load_video_info_thread(self):
        """! @brief Spawns thread for metadata fetching. """
        url = self.view.entry_url.get()
        if url: threading.Thread(target=self._fetch_thumbnail_task, args=(url,), daemon=True).start()

    def _fetch_thumbnail_task(self, url):
        """! @brief Background task to fetch info from yt-dlp. """
        try:
            self.view.lbl_status.configure(text="Fetching Info...", text_color="yellow")
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist'}) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Unknown')
            thumb = info.get('thumbnail')
            _type = info.get('_type', 'video')

            if _type == 'playlist' and info.get('thumbnails'):
                thumb = info['thumbnails'][-1]['url']

            # Playlist Detection Logic
            is_mix = "list=RD" in url or "list=UL" in url
            if _type == 'playlist' and not is_mix:
                self.detected_playlist_mode = True
                self.view.btn_std_select.configure(state="normal", text="Select Videos (Ready)")
            else:
                self.detected_playlist_mode = False
                self.view.btn_std_select.configure(state="disabled", text="Select Videos (Playlist Only)")

            # Update View
            if thumb:
                response = requests.get(thumb)
                pil = Image.open(BytesIO(response.content)).resize((250, 140))
                import customtkinter as ctk
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(250, 140))
                self.view.lbl_thumbnail.configure(image=img, text="")

            self.view.lbl_video_title.configure(text=title[:50])
            self.view.lbl_status.configure(text="Ready", text_color="gray")

        except:
            self.view.lbl_status.configure(text="Could not load info", text_color="red")
            self.detected_playlist_mode = False
            self.view.btn_std_select.configure(state="disabled", text="Select Videos (Error)")

    # --- TRACK EDITOR ---

    def launch_track_editor(self):
        """! @brief Prepares and launches the Track Editor popup. """
        url = self.view.entry_url.get()
        if not url: return

        btn = self.view.btn_edit_tracks if self.view.tab_view.get() == "Music Album Maker" else self.view.btn_std_select
        btn.configure(state="disabled", text="Fetching...")
        threading.Thread(target=self._fetch_tracks_task, args=(url, btn), daemon=True).start()

    def _fetch_tracks_task(self, url, btn):
        """! @brief Background task to fetch playlist items. """
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            tracks = [e.get('title') for e in info['entries']] if 'entries' in info else [info.get('title')]

            self.view.after(0, lambda: TrackEditorDialog(self.view, tracks, self._save_tracks_callback))
        except:
            self.view.lbl_status.configure(text="Fetch Error", text_color="red")

        default_text = "Select Videos (Ready)" if self.detected_playlist_mode else "Fetch Tracklist"
        btn.configure(state="normal", text=default_text)

    def _save_tracks_callback(self, new_titles, download_states):
        """! @brief Callback when user saves changes in Editor. """
        self.custom_tracks = new_titles
        indices = [str(i+1) for i, state in enumerate(download_states) if state == 1]

        if len(indices) == len(download_states):
            self.selected_indices_str = None
            self.selected_count = None
        else:
            self.selected_indices_str = ",".join(indices)
            self.selected_count = len(indices)

        self.view.lbl_status.configure(text=f"Selected {len(indices)} tracks.", text_color="green")

    # --- DOWNLOAD PROCESS ---

    def start_download_thread(self):
        """! @brief Main entry point for starting download. """
        if self.is_downloading == 1: return
        self.cancel_download = 0
        self.view.btn_open_folder.configure(state="disabled", text_color="gray")
        self.overwrite_permission = None

        # Reset UI
        self.view.progress_bar.set(0)
        self.view.progress_bar_playlist.set(0)
        self.view.lbl_file_stats.configure(text="")

        # Reset Internal Counter
        self.internal_download_count = 0
        self.current_file_id = None

        # Hide playlist bars initially
        self.view.lbl_playlist_status.pack_forget()
        self.view.progress_bar_playlist.pack_forget()

        url = self.view.entry_url.get()
        if not url: return

        self.is_downloading = 1
        self.view.btn_download.configure(state="disabled", text="Running...")
        self.view.btn_stop.configure(state="normal", fg_color="red")

        threading.Thread(target=self._execute_download_task, args=(url,), daemon=True).start()

    def stop_download(self):
        """! @brief Sets flag to cancel download. """
        if self.is_downloading:
            self.cancel_download = 1
            self.view.lbl_status.configure(text="Stopping...", text_color="yellow")
            self.view.btn_stop.configure(state="disabled")

    def _execute_download_task(self, url):
        """! @brief The heavy lifting download logic. """
        try:
            base_folder = self.view.entry_folder.get()
            tab = self.view.tab_view.get()

            # Build Configuration
            config = {
                'url': url,
                'folder': base_folder,
                'mode': "album" if tab == "Music Album Maker" else "standard",
                'detected_playlist': self.detected_playlist_mode,
                'format_type': "audio" if "Audio" in self.view.opt_format.get() else "video",
                'quality': self.view.opt_album_quality.get() if tab == "Music Album Maker" else self.view.opt_quality.get(),
                'selected_indices': self.selected_indices_str
            }

            # 1. Setup Dynamic Labels
            is_playlist_job = False
            if config['mode'] == "album":
                is_playlist_job = True
                self.active_progress_prefix = "Album Progress"
                self.active_item_label = "Track"
            elif config['mode'] == "standard" and config['detected_playlist']:
                is_playlist_job = True
                self.active_progress_prefix = "Playlist Progress"
                self.active_item_label = "Audio" if config['format_type'] == "audio" else "Video"

            if is_playlist_job:
                self.view.lbl_playlist_status.pack(anchor="w")
                self.view.progress_bar_playlist.pack(fill="x", pady=(2, 5))

            # 2. Mix Blocker
            is_mix = "list=RD" in url or "list=UL" in url
            if is_playlist_job and is_mix:
                 self.view.after(0, lambda: messagebox.showerror("Error", "Infinite Mixes are not supported as Playlists."))
                 raise Exception("Mix Error")

            # 3. Path Logic
            if config['mode'] == "album":
                art = self.view.entry_artist.get().strip()
                alb = self.view.entry_album.get().strip()
                if not art or not alb: raise Exception("Artist/Album missing")
                config['folder'] = os.path.join(base_folder, f"{art} - {alb}")
            elif config['mode'] == "standard" and config['detected_playlist']:
                title = download_manager.fetch_playlist_title(url) or "Playlist"
                config['folder'] = os.path.join(base_folder, title)

            self.final_download_path = config['folder']
            if not os.path.exists(config['folder']): os.makedirs(config['folder'])

            # 4. Run
            self.view.lbl_status.configure(text="Starting...", text_color=TEXT_WHITE)
            download_manager.run_downloader(config, self._progress_hook)

            self._finish(True)

        except Exception as e:
            if "Mix Error" in str(e): pass
            elif "User Cancelled" in str(e): self.view.lbl_status.configure(text="Cancelled", text_color="yellow")
            else:
                print(e)
                self.view.lbl_status.configure(text="Error", text_color="red")
            self._finish(False)

    def _progress_hook(self, d):
        """! @brief Callback called by yt-dlp during download. """
        if self.cancel_download: raise Exception("User Cancelled")

        if d['status'] == 'downloading':
            try:
                # File Stats
                p = float(d.get('_percent_str', '0%').replace('%', '')) / 100
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                title = d.get('info_dict', {}).get('title', 'Unknown')

                self.view.progress_bar.set(p)
                self.view.lbl_file_stats.configure(text=f"{int(p*100)}%  |  {speed}  |  ETA: {eta}")
                self.view.lbl_status.configure(text=f"Downloading: {title[:40]}...")

                # --- PLAYLIST PROGRESS LOGIC ---
                # Check for ID change to increment our internal counter
                # We do this because yt-dlp sends the ORIGINAL playlist index, which confuses users if filtering.
                info = d.get('info_dict', {})
                file_id = info.get('id')

                if file_id != self.current_file_id:
                    self.current_file_id = file_id
                    self.internal_download_count += 1

                # Determine total items
                # If user selected items, use that count. Else use yt-dlp total.
                total_count = self.selected_count if self.selected_count else (info.get('playlist_count') or info.get('n_entries'))

                # Update if we have a valid total (implies playlist mode)
                if total_count and total_count > 1:
                    # Calculate "Smoothed" total progress
                    # (completed_tracks + current_track_percentage) / total_tracks
                    # NOTE: We use internal_download_count - 1 because "1" means we are working on the first one (0 completed)
                    current_idx = self.internal_download_count
                    total_progress = (current_idx - 1 + p) / total_count

                    self.view.progress_bar_playlist.set(total_progress)
                    self.view.lbl_playlist_status.configure(
                        text=f"{self.active_progress_prefix}: {self.active_item_label} {current_idx} of {total_count}"
                    )
            except Exception: pass

        elif d['status'] == 'finished':
            self.view.lbl_status.configure(text="Processing...", text_color="yellow")
            self.view.progress_bar.set(1.0)

    def _finish(self, success):
        """! @brief cleanup after download thread ends. """
        self.is_downloading = 0
        self.view.btn_download.configure(state="normal", text="START DOWNLOAD")
        self.view.btn_stop.configure(state="disabled", fg_color="gray")

        if success:
            self.view.lbl_status.configure(text="Complete!", text_color="green")
            self.view.btn_open_folder.configure(state="normal", text_color=TEXT_WHITE, border_color=YT_RED)
            self.view.progress_bar.set(1.0)
            self.view.progress_bar_playlist.set(1.0)
            self.view.lbl_file_stats.configure(text="Done.")
            self.view.lbl_playlist_status.configure(text="All files downloaded.")

            # Post-Processing
            if self.view.tab_view.get() == "Music Album Maker":
                meta = {
                    'artist': self.view.entry_artist.get(),
                    'album': self.view.entry_album.get(),
                    'year': self.view.entry_year.get(),
                    'cover_path': self.cover_art_path
                }
                tag_manager.process_album_tags(self.final_download_path, meta, self.custom_tracks, lambda t: self.view.lbl_status.configure(text=t))

            # Reset
            self.custom_tracks = None
            self.selected_indices_str = None
            self.selected_count = None