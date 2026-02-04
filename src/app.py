"""!
@file app.py
@brief Main application GUI controller.
@details Coordinates UI interactions and delegates logic to managers.
"""

import customtkinter as ctk
import threading
import os
import shutil
import requests
import yt_dlp
from PIL import Image
from io import BytesIO
from tkinter import filedialog, messagebox

# OS Specific Imports
if os.name == 'nt':
    import ctypes

# Local Modules
from settings import *
from utils import get_bin_path
from ui_components import TrackEditorDialog
import download_manager
import tag_manager

class DownloaderApp(ctk.CTk):
    """!
    @brief The primary Application Class.
    """

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.configure(fg_color=YT_BG)
        self.resizable(0, 0)

        if os.name == 'nt':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
                icon_path = get_bin_path("icon.ico")
                if os.path.exists(icon_path): self.iconbitmap(icon_path)
            except: pass

        # State
        self.is_downloading = 0
        self.cancel_download = 0
        self.target_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.cover_art_path = ""
        self.custom_tracks = None
        self.selected_indices_str = None
        self.overwrite_permission = None
        self.detected_playlist_mode = False # True if URL is a valid playlist

        self.create_widgets()
        self.check_ffmpeg_integrity()

    def create_widgets(self):
        # --- Header ---
        self.lbl_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"), text_color=TEXT_WHITE)
        self.lbl_title.pack(pady=(15, 10))

        # --- URL Input ---
        self.frame_url = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url.pack(pady=5)

        self.entry_url = ctk.CTkEntry(self.frame_url, placeholder_text="Paste Link Here", width=420, fg_color=YT_SEC, text_color=TEXT_WHITE, border_width=1)
        self.entry_url.grid(row=0, column=0, padx=5)
        self.entry_url.bind("<Return>", lambda e: self.load_video_info_thread())
        self.entry_url.bind("<Control-v>", lambda e: self.after(100, self.load_video_info_thread))

        self.btn_paste = ctk.CTkButton(self.frame_url, text="Paste", width=80, command=self.paste_and_load, fg_color=YT_SEC, hover_color="gray")
        self.btn_paste.grid(row=0, column=1, padx=5)

        # --- Preview Area ---
        self.frame_preview = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_preview.pack(pady=5)

        self.lbl_thumbnail = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_thumbnail.grid(row=0, column=0, padx=10)

        self.lbl_video_title = ctk.CTkLabel(self, text="", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_video_title.pack(pady=(0, 5))

        # --- Tabs ---
        self.tab_view = ctk.CTkTabview(self, width=580, height=320, fg_color=YT_SEC, segmented_button_fg_color=YT_BG, segmented_button_selected_color=YT_RED)
        self.tab_view.pack(pady=5)
        self.tab_std = self.tab_view.add("Standard Download")
        self.tab_album = self.tab_view.add("Music Album Maker")

        # === Standard Tab ===
        ctk.CTkLabel(self.tab_std, text="Standard: Video or Audio download.", text_color="gray").pack(pady=5)

        self.opt_format = ctk.CTkOptionMenu(self.tab_std, values=["Video (MP4)", "Audio Only (MP3)"], command=self.update_quality_options, fg_color=YT_RED, width=200)
        self.opt_format.pack(pady=5)

        self.opt_quality = ctk.CTkOptionMenu(self.tab_std, values=["1080p", "720p", "480p", "360p"], fg_color=YT_BG, width=200)
        self.opt_quality.pack(pady=5)

        # New: "Select Videos" button - Disabled by default
        self.btn_std_select = ctk.CTkButton(self.tab_std, text="Select Videos (Playlist Only)", command=self.launch_track_editor, fg_color=YT_BG, hover_color="gray", state="disabled", width=200)
        self.btn_std_select.pack(pady=15)

        # === Album Tab ===
        ctk.CTkLabel(self.tab_album, text="Album: Creates 'Artist - Album' folder.", text_color="gray").pack(pady=2)

        self.entry_artist = ctk.CTkEntry(self.tab_album, placeholder_text="Artist Name", width=300)
        self.entry_artist.pack(pady=5)
        self.entry_album = ctk.CTkEntry(self.tab_album, placeholder_text="Album Name", width=300)
        self.entry_album.pack(pady=5)
        self.entry_year = ctk.CTkEntry(self.tab_album, placeholder_text="Year", width=300)
        self.entry_year.pack(pady=5)

        self.opt_album_quality = ctk.CTkOptionMenu(self.tab_album, values=["320kbps", "192kbps", "128kbps"], fg_color=YT_BG)
        self.opt_album_quality.set("192kbps")
        self.opt_album_quality.pack(pady=5)

        self.frame_alb_btns = ctk.CTkFrame(self.tab_album, fg_color="transparent")
        self.frame_alb_btns.pack(pady=5)
        ctk.CTkButton(self.frame_alb_btns, text="Select Cover Art", command=self.select_cover_art, fg_color=YT_BG, width=140).grid(row=0, column=0, padx=5)
        self.btn_edit_tracks = ctk.CTkButton(self.frame_alb_btns, text="Fetch Tracklist", command=self.launch_track_editor, fg_color=YT_BG, border_width=1, border_color=YT_RED, width=140)
        self.btn_edit_tracks.grid(row=0, column=1, padx=5)

        # --- Folder Selection ---
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=5)

        self.entry_folder = ctk.CTkEntry(self.frame_folder, width=380, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_folder.insert(0, self.target_folder)
        self.entry_folder.grid(row=0, column=0, padx=5)

        ctk.CTkButton(self.frame_folder, text="Browse", width=80, command=self.browse_folder, fg_color=YT_SEC).grid(row=0, column=1, padx=5)

        # --- Main Action Buttons (Restored) ---
        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.pack(pady=10)

        # Start Button
        self.btn_download = ctk.CTkButton(self.frame_actions, text="START DOWNLOAD", command=self.start_thread, fg_color=YT_RED, hover_color=YT_RED_HOVER, width=180, height=40, font=("Arial", 14, "bold"))
        self.btn_download.grid(row=0, column=0, padx=10)

        # Stop Button
        self.btn_stop = ctk.CTkButton(self.frame_actions, text="STOP", command=self.stop_download, fg_color="gray", state="disabled", width=80, height=40, font=("Arial", 12, "bold"))
        self.btn_stop.grid(row=0, column=1, padx=10)

        # Open Folder Button
        self.btn_open_folder = ctk.CTkButton(self.frame_actions, text="Open Folder", command=self.open_target_folder, fg_color="transparent", border_width=1, border_color="gray", text_color="gray", width=100, height=40, state="disabled")
        self.btn_open_folder.grid(row=0, column=2, padx=10)

        # --- Status Bar ---
        self.progress_bar = ctk.CTkProgressBar(self, width=550, progress_color=YT_RED)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Arial", 14))
        self.lbl_status.pack(pady=5)
        self.lbl_detail_status = ctk.CTkLabel(self, text="", text_color="gray", font=("Arial", 11))
        self.lbl_detail_status.pack(pady=0)

    # --- HELPER FUNCTIONS ---
    def check_ffmpeg_integrity(self):
        if os.name == 'nt':
            if not os.path.exists(get_bin_path("ffmpeg.exe")):
                self.lbl_status.configure(text="Error: bin/ffmpeg.exe missing!", text_color="red")
                self.btn_download.configure(state="disabled")
        else:
            if not shutil.which("ffmpeg"):
                self.lbl_status.configure(text="Error: ffmpeg missing!", text_color="red")
                self.btn_download.configure(state="disabled")

    def update_quality_options(self, choice):
        if choice == "Video (MP4)":
            self.opt_quality.configure(values=["1080p", "720p", "480p", "360p"])
            self.opt_quality.set("1080p")
        else:
            self.opt_quality.configure(values=["320kbps", "192kbps", "128kbps"])
            self.opt_quality.set("192kbps")

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.target_folder = f
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, f)

    def select_cover_art(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
        if f: self.cover_art_path = f

    def open_target_folder(self):
        path = getattr(self, 'final_download_path', self.entry_folder.get())
        if os.path.exists(path):
            if os.name == 'nt': os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])

    def stop_download(self):
        if self.is_downloading:
            self.cancel_download = 1
            self.lbl_status.configure(text="Stopping...", text_color="yellow")
            self.btn_stop.configure(state="disabled")

    def paste_and_load(self):
        try:
            self.entry_url.delete(0, "end")
            self.entry_url.insert(0, self.clipboard_get())
            self.load_video_info_thread()
        except: pass

    def load_video_info_thread(self):
        url = self.entry_url.get()
        if url: threading.Thread(target=self.fetch_thumbnail, args=(url,), daemon=True).start()

    def fetch_thumbnail(self, url):
        """!
        @brief Fetches thumbnail AND detects if URL is a playlist/mix.
        """
        try:
            self.lbl_status.configure(text="Fetching Info...", text_color="yellow")

            # 1. Fetch Info
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist'}) as ydl:
                info = ydl.extract_info(url, download=False)

            # 2. Extract Data
            title = info.get('title', 'Unknown')
            thumb = info.get('thumbnail')
            _type = info.get('_type', 'video')

            # 3. Handle Playlist Thumbnails
            if _type == 'playlist' and info.get('thumbnails'):
                thumb = info['thumbnails'][-1]['url']

            # 4. Detect Playlist Mode (Auto-Enable/Disable Button)
            # Logic: If it is a playlist AND NOT a Mix (RD/UL), enable selection.
            is_mix = "list=RD" in url or "list=UL" in url

            if _type == 'playlist' and not is_mix:
                self.detected_playlist_mode = True
                self.btn_std_select.configure(state="normal", text="Select Videos (Ready)")
            else:
                self.detected_playlist_mode = False
                self.btn_std_select.configure(state="disabled", text="Select Videos (Playlist Only)")

            # 5. Update UI (Thumbnail)
            if thumb:
                response = requests.get(thumb)
                pil = Image.open(BytesIO(response.content)).resize((250, 140))
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(250, 140))
                self.lbl_thumbnail.configure(image=img, text="")

            self.lbl_video_title.configure(text=title[:50])
            self.lbl_status.configure(text="Ready", text_color="gray")

        except Exception as e:
            # print(e) # Debug
            self.lbl_status.configure(text="Could not load info", text_color="red")
            self.detected_playlist_mode = False
            self.btn_std_select.configure(state="disabled", text="Select Videos (Error)")

    # --- TRACK EDITOR LOGIC ---
    def launch_track_editor(self):
        url = self.entry_url.get()
        if not url: return

        btn = self.btn_edit_tracks if self.tab_view.get() == "Music Album Maker" else self.btn_std_select
        btn.configure(state="disabled", text="Fetching...")
        threading.Thread(target=self.fetch_tracks, args=(url, btn), daemon=True).start()

    def fetch_tracks(self, url, btn):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            tracks = [e.get('title') for e in info['entries']] if 'entries' in info else [info.get('title')]
            self.after(0, lambda: TrackEditorDialog(self, tracks, self.save_tracks))
        except:
            self.lbl_status.configure(text="Fetch Error", text_color="red")

        # Reset button text based on mode
        default_text = "Select Videos (Ready)" if self.detected_playlist_mode else "Fetch Tracklist"
        btn.configure(state="normal", text=default_text)

    def save_tracks(self, new_titles, download_states):
        self.custom_tracks = new_titles
        indices = [str(i+1) for i, state in enumerate(download_states) if state == 1]

        if len(indices) == len(download_states):
            self.selected_indices_str = None
        else:
            self.selected_indices_str = ",".join(indices)

        self.lbl_status.configure(text=f"Selected {len(indices)} tracks.", text_color="green")

    # --- DOWNLOAD LOGIC ---
    def start_thread(self):
        if self.is_downloading == 1: return
        self.cancel_download = 0
        self.btn_open_folder.configure(state="disabled", text_color="gray")
        self.overwrite_permission = None

        url = self.entry_url.get()
        if not url: return

        self.is_downloading = 1
        self.btn_download.configure(state="disabled", text="Running...")
        self.btn_stop.configure(state="normal", fg_color="red")

        threading.Thread(target=self.execute_logic, args=(url,), daemon=True).start()

    def execute_logic(self, url):
        try:
            base_folder = self.entry_folder.get()
            tab = self.tab_view.get()

            # 1. Config Object
            config = {
                'url': url,
                'folder': base_folder,
                'mode': "album" if tab == "Music Album Maker" else "standard",
                'detected_playlist': self.detected_playlist_mode, # Passed from detection
                'format_type': "audio" if "Audio" in self.opt_format.get() else "video",
                'quality': self.opt_album_quality.get() if tab == "Music Album Maker" else self.opt_quality.get(),
                'selected_indices': self.selected_indices_str
            }

            # 2. Check for Infinite Mix
            # If we are in Album mode OR (Standard mode AND it looks like a playlist), we must block Mixes.
            is_mix = "list=RD" in url or "list=UL" in url
            if (config['mode'] == "album" or config['detected_playlist']) and is_mix:
                 self.after(0, lambda: messagebox.showerror("Error", "Infinite Mixes are not supported as Playlists."))
                 raise Exception("Mix Error")

            # 3. Path Logic
            if config['mode'] == "album":
                art = self.entry_artist.get().strip()
                alb = self.entry_album.get().strip()
                if not art or not alb: raise Exception("Artist/Album missing")
                config['folder'] = os.path.join(base_folder, f"{art} - {alb}")

            elif config['mode'] == "standard" and config['detected_playlist']:
                # Only create subfolder if it is a REAL playlist
                title = download_manager.fetch_playlist_title(url) or "Playlist"
                config['folder'] = os.path.join(base_folder, title)

            self.final_download_path = config['folder']

            # 4. Create Folder
            if not os.path.exists(config['folder']):
                os.makedirs(config['folder'])

            # 5. Run Download
            self.lbl_status.configure(text="Downloading...", text_color=TEXT_WHITE)
            download_manager.run_downloader(config, self.progress_hook)

            # 6. Success
            self.finish(True)

        except Exception as e:
            if "Mix Error" in str(e): pass
            elif "User Cancelled" in str(e): self.lbl_status.configure(text="Cancelled", text_color="yellow")
            else:
                print(e)
                self.lbl_status.configure(text="Error", text_color="red")
            self.finish(False)

    def progress_hook(self, d):
        if self.cancel_download: raise Exception("User Cancelled")
        if d['status'] == 'downloading':
            try:
                p = float(d.get('_percent_str', '0%').replace('%', '')) / 100
                self.progress_bar.set(p)
                self.lbl_status.configure(text=f"Downloading: {d.get('info_dict', {}).get('title', '')[:30]}...")
            except: pass

    def finish(self, success):
        self.is_downloading = 0
        self.btn_download.configure(state="normal", text="START DOWNLOAD")
        self.btn_stop.configure(state="disabled", fg_color="gray")
        self.progress_bar.set(0)

        if success:
            self.lbl_status.configure(text="Complete!", text_color="green")
            self.btn_open_folder.configure(state="normal", text_color=TEXT_WHITE, border_color=YT_RED)

            # Run Tagging if Album Mode
            if self.tab_view.get() == "Music Album Maker":
                meta = {
                    'artist': self.entry_artist.get(),
                    'album': self.entry_album.get(),
                    'year': self.entry_year.get(),
                    'cover_path': self.cover_art_path
                }
                tag_manager.process_album_tags(self.final_download_path, meta, self.custom_tracks, lambda t: self.lbl_status.configure(text=t))

            self.custom_tracks = None
            self.selected_indices_str = None