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

        self.create_widgets()
        self.check_ffmpeg_integrity()

    def create_widgets(self):
        # Header
        self.lbl_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"), text_color=TEXT_WHITE)
        self.lbl_title.pack(pady=10)

        # URL
        self.frame_url = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url.pack(pady=5)
        self.entry_url = ctk.CTkEntry(self.frame_url, placeholder_text="Paste Link Here", width=400, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_url.grid(row=0, column=0, padx=5)
        self.entry_url.bind("<Return>", lambda e: self.load_video_info_thread())
        self.entry_url.bind("<Control-v>", lambda e: self.after(100, self.load_video_info_thread))
        self.btn_paste = ctk.CTkButton(self.frame_url, text="Paste Link", width=80, command=self.paste_and_load, fg_color=YT_SEC)
        self.btn_paste.grid(row=0, column=1, padx=5)

        # Preview
        self.frame_preview = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_preview.pack(pady=5)
        self.lbl_thumbnail = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_thumbnail.grid(row=0, column=0, padx=10)
        self.lbl_video_title = ctk.CTkLabel(self, text="", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_video_title.pack(pady=0)

        # Tabs
        self.tab_view = ctk.CTkTabview(self, width=550, height=350, fg_color=YT_SEC, segmented_button_fg_color=YT_BG, segmented_button_selected_color=YT_RED)
        self.tab_view.pack(pady=10)
        self.tab_std = self.tab_view.add("Standard Download")
        self.tab_album = self.tab_view.add("Music Album Maker")

        # Standard Tab
        ctk.CTkLabel(self.tab_std, text="Standard: Auto-creates folders for Playlists.", text_color="gray").pack(pady=5)
        self.opt_format = ctk.CTkOptionMenu(self.tab_std, values=["Video (MP4)", "Audio Only (MP3)"], command=self.update_quality_options, fg_color=YT_RED)
        self.opt_format.pack(pady=5)
        self.opt_quality = ctk.CTkOptionMenu(self.tab_std, values=["1080p", "720p", "480p", "360p"], fg_color=YT_SEC)
        self.opt_quality.pack(pady=5)
        self.check_playlist = ctk.CTkCheckBox(self.tab_std, text="Download as Playlist / Mix", onvalue=1, offvalue=0)
        self.check_playlist.select()
        self.check_playlist.pack(pady=10)
        self.btn_std_select = ctk.CTkButton(self.tab_std, text="Select Videos / Edit Names", command=self.launch_track_editor, fg_color=YT_SEC)
        self.btn_std_select.pack(pady=5)

        # Album Tab
        ctk.CTkLabel(self.tab_album, text="Album: Creates 'Artist - Album' folder.", text_color="gray").pack(pady=2)
        self.entry_artist = ctk.CTkEntry(self.tab_album, placeholder_text="Artist Name", width=300)
        self.entry_artist.pack(pady=5)
        self.entry_album = ctk.CTkEntry(self.tab_album, placeholder_text="Album Name", width=300)
        self.entry_album.pack(pady=5)
        self.entry_year = ctk.CTkEntry(self.tab_album, placeholder_text="Year", width=300)
        self.entry_year.pack(pady=5)
        self.opt_album_quality = ctk.CTkOptionMenu(self.tab_album, values=["320kbps", "192kbps", "128kbps"], fg_color=YT_SEC)
        self.opt_album_quality.set("192kbps")
        self.opt_album_quality.pack(pady=5)

        self.frame_alb_btns = ctk.CTkFrame(self.tab_album, fg_color="transparent")
        self.frame_alb_btns.pack(pady=5)
        ctk.CTkButton(self.frame_alb_btns, text="Select Cover Art", command=self.select_cover_art, fg_color=YT_SEC, width=140).grid(row=0, column=0, padx=5)
        self.btn_edit_tracks = ctk.CTkButton(self.frame_alb_btns, text="Fetch & Edit Tracklist", command=self.launch_track_editor, fg_color=YT_SEC, border_width=1, border_color=YT_RED, width=140)
        self.btn_edit_tracks.grid(row=0, column=1, padx=5)

        # Folder & Actions
        self.entry_folder = ctk.CTkEntry(self, width=350, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_folder.insert(0, self.target_folder)
        self.entry_folder.pack(pady=5)
        ctk.CTkButton(self, text="Browse", width=100, command=self.browse_folder, fg_color=YT_SEC).pack(pady=5)

        self.btn_download = ctk.CTkButton(self, text="START DOWNLOAD", command=self.start_thread, fg_color=YT_RED, width=180, height=40, font=("Arial", 14, "bold"))
        self.btn_download.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self, width=500, progress_color=YT_RED)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Arial", 14))
        self.lbl_status.pack(pady=5)

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
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            thumb = info.get('thumbnail')
            if info.get('_type') == 'playlist' and info.get('thumbnails'):
                thumb = info['thumbnails'][-1]['url']

            if thumb:
                response = requests.get(thumb)
                pil = Image.open(BytesIO(response.content)).resize((250, 140))
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(250, 140))
                self.lbl_thumbnail.configure(image=img, text="")
            self.lbl_video_title.configure(text=title[:50])
        except: pass

    # --- TRACK EDITOR LOGIC ---
    def launch_track_editor(self):
        url = self.entry_url.get()
        if not url: return
        # Check Mix
        if "list=RD" in url or "list=UL" in url:
            messagebox.showerror("Error", "Mixes cannot be edited (Infinite).")
            return

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
        btn.configure(state="normal", text="Select Videos / Edit Names")

    def save_tracks(self, new_titles, download_states):
        self.custom_tracks = new_titles
        indices = [str(i+1) for i, state in enumerate(download_states) if state == 1]
        if len(indices) == len(download_states): self.selected_indices_str = None
        else: self.selected_indices_str = ",".join(indices)
        self.lbl_status.configure(text=f"Selected {len(indices)} tracks.", text_color="green")

    # --- DOWNLOAD LOGIC ---
    def start_thread(self):
        if self.is_downloading == 1: return
        self.cancel_download = 0
        url = self.entry_url.get()
        if not url: return

        self.is_downloading = 1
        self.btn_download.configure(state="disabled", text="Running...")
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
                'is_playlist_mode': self.check_playlist.get(),
                'format_type': "audio" if "Audio" in self.opt_format.get() else "video",
                'quality': self.opt_album_quality.get() if tab == "Music Album Maker" else self.opt_quality.get(),
                'selected_indices': self.selected_indices_str
            }

            # 2. Check for Infinite Mix
            if config['mode'] == "standard" and config['is_playlist_mode'] and ("list=RD" in url or "list=UL" in url):
                self.after(0, lambda: messagebox.showerror("Error", "Infinite Mixes not supported as Playlists."))
                raise Exception("Mix Error")

            # 3. Path Logic
            if config['mode'] == "album":
                art = self.entry_artist.get().strip()
                alb = self.entry_album.get().strip()
                if not art or not alb: raise Exception("Artist/Album missing")
                config['folder'] = os.path.join(base_folder, f"{art} - {alb}")
            elif config['mode'] == "standard" and config['is_playlist_mode'] and "list=" in url:
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
        self.progress_bar.set(0)

        if success:
            self.lbl_status.configure(text="Complete!", text_color="green")
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