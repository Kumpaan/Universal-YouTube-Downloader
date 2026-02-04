"""!
@file view.py
@brief Defines the visual structure of the application.
@details Contains the DownloaderView class which initializes all CustomTkinter widgets.
"""

import customtkinter as ctk
import os
from settings import *
from utils import get_bin_path

# Windows Taskbar Icon Fix
if os.name == 'nt':
    import ctypes


class DownloaderView(ctk.CTk):
    """!
    @brief The Main Window Class (GUI Only).
    @details Sets up the window geometry, themes, and all UI widgets.
    Does not handle button clicks logic directly.
    """

    def __init__(self):
        """!
        @brief Initialize the main window and UI components.
        """
        super().__init__()

        # --- Window Setup ---
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.configure(fg_color=YT_BG)
        self.resizable(0, 0)

        self._setup_icon()
        self._create_widgets()

    def _setup_icon(self):
        """!
        @brief Sets the application icon and AppID for Windows.
        """
        if os.name == 'nt':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
                icon_path = get_bin_path("icon.ico")
                if os.path.exists(icon_path): self.iconbitmap(icon_path)
            except Exception:
                pass

    def _create_widgets(self):
        """!
        @brief Instantiates and places all widgets on the grid/pack layout.
        """
        # --- Header ---
        self.lbl_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"),
                                      text_color=TEXT_WHITE)
        self.lbl_title.pack(pady=(15, 10))

        # --- URL Input ---
        self.frame_url = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url.pack(pady=5)

        self.entry_url = ctk.CTkEntry(self.frame_url, placeholder_text="Paste Link Here", width=420, fg_color=YT_SEC,
                                      text_color=TEXT_WHITE, border_width=1)
        self.entry_url.grid(row=0, column=0, padx=5)

        self.btn_paste = ctk.CTkButton(self.frame_url, text="Paste", width=80, fg_color=YT_SEC, hover_color="gray")
        self.btn_paste.grid(row=0, column=1, padx=5)

        # --- Preview Area ---
        self.frame_preview = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_preview.pack(pady=5)

        self.lbl_thumbnail = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_thumbnail.grid(row=0, column=0, padx=10)

        self.lbl_video_title = ctk.CTkLabel(self, text="", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_video_title.pack(pady=(0, 5))

        # --- Tabs ---
        self.tab_view = ctk.CTkTabview(self, width=580, height=320, fg_color=YT_SEC, segmented_button_fg_color=YT_BG,
                                       segmented_button_selected_color=YT_RED)
        self.tab_view.pack(pady=5)
        self.tab_std = self.tab_view.add("Standard Download")
        self.tab_album = self.tab_view.add("Music Album Maker")

        # === Standard Tab ===
        ctk.CTkLabel(self.tab_std, text="Standard: Video or Audio download.", text_color="gray").pack(pady=5)

        self.opt_format = ctk.CTkOptionMenu(self.tab_std, values=["Video (MP4)", "Audio Only (MP3)"], fg_color=YT_RED,
                                            width=200)
        self.opt_format.pack(pady=5)

        self.opt_quality = ctk.CTkOptionMenu(self.tab_std, values=["1080p", "720p", "480p", "360p"], fg_color=YT_BG,
                                             width=200)
        self.opt_quality.pack(pady=5)

        self.btn_std_select = ctk.CTkButton(self.tab_std, text="Select Videos (Playlist Only)", fg_color=YT_BG,
                                            hover_color="gray", state="disabled", width=200)
        self.btn_std_select.pack(pady=15)

        # === Album Tab ===
        ctk.CTkLabel(self.tab_album, text="Album: Creates 'Artist - Album' folder.", text_color="gray").pack(pady=2)

        self.entry_artist = ctk.CTkEntry(self.tab_album, placeholder_text="Artist Name", width=300)
        self.entry_artist.pack(pady=5)
        self.entry_album = ctk.CTkEntry(self.tab_album, placeholder_text="Album Name", width=300)
        self.entry_album.pack(pady=5)
        self.entry_year = ctk.CTkEntry(self.tab_album, placeholder_text="Year", width=300)
        self.entry_year.pack(pady=5)

        self.opt_album_quality = ctk.CTkOptionMenu(self.tab_album, values=["320kbps", "192kbps", "128kbps"],
                                                   fg_color=YT_BG)
        self.opt_album_quality.set("192kbps")
        self.opt_album_quality.pack(pady=5)

        self.frame_alb_btns = ctk.CTkFrame(self.tab_album, fg_color="transparent")
        self.frame_alb_btns.pack(pady=5)
        self.btn_cover = ctk.CTkButton(self.frame_alb_btns, text="Select Cover Art", fg_color=YT_BG, width=140)
        self.btn_cover.grid(row=0, column=0, padx=5)
        self.btn_edit_tracks = ctk.CTkButton(self.frame_alb_btns, text="Fetch Tracklist", fg_color=YT_BG,
                                             border_width=1, border_color=YT_RED, width=140)
        self.btn_edit_tracks.grid(row=0, column=1, padx=5)

        # --- Folder Selection ---
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=5)

        self.entry_folder = ctk.CTkEntry(self.frame_folder, width=380, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_folder.grid(row=0, column=0, padx=5)

        self.btn_browse = ctk.CTkButton(self.frame_folder, text="Browse", width=80, fg_color=YT_SEC)
        self.btn_browse.grid(row=0, column=1, padx=5)

        # --- Main Action Buttons ---
        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.pack(pady=10)

        self.btn_download = ctk.CTkButton(self.frame_actions, text="START DOWNLOAD", fg_color=YT_RED,
                                          hover_color=YT_RED_HOVER, width=180, height=40, font=("Arial", 14, "bold"))
        self.btn_download.grid(row=0, column=0, padx=10)

        self.btn_stop = ctk.CTkButton(self.frame_actions, text="STOP", fg_color="gray", state="disabled", width=80,
                                      height=40, font=("Arial", 12, "bold"))
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.btn_open_folder = ctk.CTkButton(self.frame_actions, text="Open Folder", fg_color="transparent",
                                             border_width=1, border_color="gray", text_color="gray", width=100,
                                             height=40, state="disabled")
        self.btn_open_folder.grid(row=0, column=2, padx=10)

        # --- Progress Section ---
        self.frame_progress = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_progress.pack(pady=5, fill="x", padx=20)

        # File Progress
        self.lbl_file_stats = ctk.CTkLabel(self.frame_progress, text="", text_color="gray", font=("Arial", 12))
        self.lbl_file_stats.pack(anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.frame_progress, height=12, progress_color=YT_RED)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(2, 10))

        # Playlist Progress (Hidden initially)
        self.lbl_playlist_status = ctk.CTkLabel(self.frame_progress, text="Playlist Progress: -/-", text_color="gray",
                                                font=("Arial", 12, "bold"))
        self.progress_bar_playlist = ctk.CTkProgressBar(self.frame_progress, height=12, progress_color=YT_RED)
        self.progress_bar_playlist.set(0)

        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Arial", 14))
        self.lbl_status.pack(pady=5)