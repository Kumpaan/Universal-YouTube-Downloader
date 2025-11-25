import customtkinter as ctk
import yt_dlp
import threading
import os
import re
import requests
import time
from PIL import Image
from io import BytesIO
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from tkinter import filedialog, messagebox

# --- Configuration & Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# YouTube Color Palette
YT_BG = "#0f0f0f"  # Pitch Black
YT_SEC = "#272727"  # Dark Gray
YT_RED = "#CC0000"  # YouTube Red
YT_RED_HOVER = "#990000"
TEXT_WHITE = "#FFFFFF"


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Universal YouTube Downloader")
        self.geometry("800x750")  # Reduced height to fit standard screens
        self.configure(fg_color=YT_BG)
        self.resizable(0, 0)

        # Logic Flags
        self.is_downloading = 0
        self.cancel_download = 0
        self.target_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.cover_art_path = ""
        self.overwrite_permission = None

        # UI Layout
        self.create_widgets()
        self.check_ffmpeg_integrity()

    def create_widgets(self):
        # 1. Title
        self.lbl_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"),
                                      text_color=TEXT_WHITE)
        self.lbl_title.pack(pady=10)

        # 2. URL Input Area
        self.frame_url = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url.pack(pady=5)

        self.entry_url = ctk.CTkEntry(self.frame_url, placeholder_text="Paste Link Here", width=400,
                                      fg_color=YT_SEC, border_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_url.grid(row=0, column=0, padx=5)

        self.entry_url.bind("<Return>", lambda event: self.load_video_info_thread())
        self.entry_url.bind("<Control-v>", lambda event: self.after(100, self.load_video_info_thread))

        self.btn_paste = ctk.CTkButton(self.frame_url, text="Paste Link", width=80, command=self.paste_and_load,
                                       fg_color=YT_SEC, hover_color="gray")
        self.btn_paste.grid(row=0, column=1, padx=5)

        # 3. Thumbnail / Preview Area
        self.frame_preview = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_preview.pack(pady=5)

        # We use two labels: One for YouTube Thumb, One for Chosen Cover Art
        self.lbl_thumbnail = ctk.CTkLabel(self.frame_preview, text="", height=1)
        self.lbl_thumbnail.grid(row=0, column=0, padx=10)

        self.lbl_cover_preview = ctk.CTkLabel(self.frame_preview, text="", height=1)  # Initially hidden
        self.lbl_cover_preview.grid(row=0, column=1, padx=10)

        self.lbl_video_title = ctk.CTkLabel(self, text="", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_video_title.pack(pady=0)

        # 4. Tabs
        self.tab_view = ctk.CTkTabview(self, width=550, height=300, fg_color=YT_SEC,
                                       segmented_button_fg_color=YT_BG, segmented_button_selected_color=YT_RED,
                                       segmented_button_selected_hover_color=YT_RED_HOVER)
        self.tab_view.pack(pady=10)

        self.tab_std = self.tab_view.add("Standard Download")
        self.tab_album = self.tab_view.add("Music Album Maker")

        # --- TAB 1: Standard ---
        self.lbl_std_info = ctk.CTkLabel(self.tab_std, text="Standard: Auto-creates folders for Playlists.",
                                         text_color="gray")
        self.lbl_std_info.pack(pady=5)
        self.opt_format = ctk.CTkOptionMenu(self.tab_std, values=["Video (MP4)", "Audio Only (MP3)"],
                                            command=self.update_quality_options, fg_color=YT_RED, button_color=YT_RED)
        self.opt_format.pack(pady=10)
        self.opt_quality = ctk.CTkOptionMenu(self.tab_std, values=["1080p", "720p", "480p", "360p"], fg_color=YT_SEC,
                                             button_color=YT_SEC)
        self.opt_quality.pack(pady=10)

        # --- TAB 2: Album Maker ---
        self.lbl_alb_info = ctk.CTkLabel(self.tab_album,
                                         text="Album: Creates 'Artist - Album' folder.\nFiles named: XX-SongName.mp3",
                                         text_color="gray")
        self.lbl_alb_info.pack(pady=5)
        self.entry_artist = ctk.CTkEntry(self.tab_album, placeholder_text="Artist Name", width=300)
        self.entry_artist.pack(pady=5)
        self.entry_album = ctk.CTkEntry(self.tab_album, placeholder_text="Album Name", width=300)
        self.entry_album.pack(pady=5)
        self.entry_year = ctk.CTkEntry(self.tab_album, placeholder_text="Year", width=300)
        self.entry_year.pack(pady=5)
        self.opt_album_quality = ctk.CTkOptionMenu(self.tab_album, values=["320kbps", "192kbps", "128kbps"],
                                                   fg_color=YT_SEC, button_color=YT_SEC)
        self.opt_album_quality.set("192kbps")
        self.opt_album_quality.pack(pady=10)

        self.btn_cover = ctk.CTkButton(self.tab_album, text="Select Cover Art", command=self.select_cover_art,
                                       fg_color=YT_SEC, hover_color="gray")
        self.btn_cover.pack(pady=5)

        # 5. Destination
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=5)
        self.entry_folder = ctk.CTkEntry(self.frame_folder, width=350, fg_color=YT_SEC, text_color=TEXT_WHITE)
        self.entry_folder.insert(0, self.target_folder)
        self.entry_folder.grid(row=0, column=0, padx=5)
        self.btn_browse = ctk.CTkButton(self.frame_folder, text="Browse", width=100, command=self.browse_folder,
                                        fg_color=YT_SEC, hover_color="gray")
        self.btn_browse.grid(row=0, column=1, padx=5)

        # 6. Actions (Buttons + Open Folder)
        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.pack(pady=15)

        self.btn_download = ctk.CTkButton(self.frame_actions, text="START DOWNLOAD", command=self.start_thread,
                                          fg_color=YT_RED, hover_color=YT_RED_HOVER, width=180, height=40,
                                          font=("Arial", 14, "bold"))
        self.btn_download.grid(row=0, column=0, padx=5)

        self.btn_stop = ctk.CTkButton(self.frame_actions, text="STOP", command=self.stop_download,
                                      fg_color="gray", state="disabled", width=80, height=40,
                                      font=("Arial", 12, "bold"))
        self.btn_stop.grid(row=0, column=1, padx=5)

        # MOVED UP: The Open Folder button is now here so it's always visible
        self.btn_open_folder = ctk.CTkButton(self.frame_actions, text="Open Folder", command=self.open_target_folder,
                                             fg_color="transparent", border_width=1, border_color="gray",
                                             text_color="gray", width=100, height=40, state="disabled")
        self.btn_open_folder.grid(row=0, column=2, padx=5)

        # Status
        self.progress_bar = ctk.CTkProgressBar(self, width=500, progress_color=YT_RED)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray", font=("Arial", 14))
        self.lbl_status.pack(pady=5)

        self.lbl_detail_status = ctk.CTkLabel(self, text="", text_color="gray", font=("Arial", 11))
        self.lbl_detail_status.pack(pady=2)

    # --- Logic ---

    def check_ffmpeg_integrity(self):
        if not os.path.exists(os.path.join(os.getcwd(), "ffmpeg.exe")):
            self.lbl_status.configure(text="CRITICAL ERROR: ffmpeg.exe missing!", text_color="red")
            self.btn_download.configure(state="disabled")

    def stop_download(self):
        if self.is_downloading:
            self.cancel_download = 1
            self.lbl_status.configure(text="Stopping...", text_color="yellow")
            self.btn_stop.configure(state="disabled")

    def update_quality_options(self, choice):
        if choice == "Video (MP4)":
            self.opt_quality.configure(values=["1080p", "720p", "480p", "360p"])
            self.opt_quality.set("1080p")
        else:
            self.opt_quality.configure(values=["320kbps", "192kbps", "128kbps"])
            self.opt_quality.set("192kbps")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder = folder
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, self.target_folder)

    def select_cover_art(self):
        img_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if img_path:
            self.cover_art_path = img_path

            # Create a Preview
            try:
                pil_image = Image.open(img_path)
                pil_image = pil_image.resize((150, 150))  # Square for cover art
                tk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
                self.lbl_cover_preview.configure(image=tk_image, text="")
                self.lbl_status.configure(text="Cover Art Selected", text_color="green")
            except:
                self.lbl_status.configure(text="Invalid Image", text_color="red")

    def open_target_folder(self):
        if hasattr(self, 'final_download_path') and os.path.exists(self.final_download_path):
            os.startfile(self.final_download_path)
        else:
            path = self.entry_folder.get()
            if os.path.exists(path):
                os.startfile(path)

    def paste_and_load(self):
        try:
            clipboard_content = self.clipboard_get()

            # Simple check to prevent pasting code
            if "import " in clipboard_content or "def " in clipboard_content:
                messagebox.showerror("Error", "You pasted Python code, not a URL!")
                return

            self.entry_url.delete(0, "end")
            self.entry_url.insert(0, clipboard_content)
            self.load_video_info_thread()
        except Exception as e:
            self.lbl_status.configure(text="Clipboard Empty", text_color="red")

    def load_video_info_thread(self):
        url = self.entry_url.get()
        if url: threading.Thread(target=self.fetch_thumbnail, args=(url,), daemon=True).start()

    def fetch_thumbnail(self, url):
        try:
            self.lbl_status.configure(text="Fetching Info...", text_color="yellow")
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info: info = info['entries'][0]
                thumb_url = info.get('thumbnail')
                title = info.get('title')

            response = requests.get(thumb_url)
            pil_image = Image.open(BytesIO(response.content)).resize((250, 140))
            tk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(250, 140))

            self.lbl_thumbnail.configure(image=tk_image, text="")
            self.lbl_video_title.configure(text=title[:50])
            self.lbl_status.configure(text="Ready", text_color="gray")
        except:
            self.lbl_status.configure(text="Could not load preview", text_color="red")

    def start_thread(self):
        if self.is_downloading == 1: return
        self.cancel_download = 0
        self.btn_open_folder.configure(state="disabled", text_color="gray")
        self.overwrite_permission = None

        url = self.entry_url.get()
        base_folder = self.entry_folder.get()

        if not url: return
        # Prevent downloading code
        if "import " in url:
            messagebox.showerror("Error", "Please paste a YouTube URL, not code.")
            return

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
        response = messagebox.askyesno("Folder Exists",
                                       f"The folder '{folder_name}' already exists.\nDo you want to write into it (merge/overwrite)?")
        self.overwrite_permission = response

    def pre_download_logic(self, url, base_folder):
        try:
            current_tab = self.tab_view.get()
            final_path = base_folder

            self.lbl_status.configure(text="Checking Paths...", text_color="yellow")

            # 1. Determine Folder Name
            if current_tab == "Music Album Maker":
                artist = self.entry_artist.get().strip()
                album = self.entry_album.get().strip()
                if not artist or not album:
                    self.lbl_status.configure(text="Error: Artist & Album Required", text_color="red")
                    self.finish_download(0)
                    return
                folder_name = f"{artist} - {album}"
                final_path = os.path.join(base_folder, folder_name)

            else:
                if "list=" in url:
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(url, download=False, process=False)
                        if info.get('_type') == 'playlist':
                            title = info.get('title', 'Unknown Playlist')
                            title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == ' ']).strip()
                            final_path = os.path.join(base_folder, title)

            # 2. Check Overwrite
            if os.path.exists(final_path):
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
            self.lbl_status.configure(text="Error fetching info", text_color="red")
            self.finish_download(0)

    def clean_title_logic(self, raw_title, artist_name):
        track_prefix = ""
        match = re.match(r'^(\d{2}-)', raw_title)
        if match:
            track_prefix = match.group(1)
            raw_title = raw_title[len(track_prefix):]

        clean = raw_title
        if artist_name and clean.lower().startswith(artist_name.lower()):
            clean = clean[len(artist_name):]
            clean = re.sub(r'^[\s\-\:]+', '', clean)
        clean = re.sub(r'\s*[\(\[].*?(official|video|lyrics|4k|hd|hq|visualizer).*?[\)\]]', '', clean,
                       flags=re.IGNORECASE)

        return track_prefix + clean.strip()

    def run_download(self, url, folder_path):
        try:
            self.lbl_status.configure(text="Starting Download...", text_color=TEXT_WHITE)
            current_tab = self.tab_view.get()

            ydl_opts = {
                'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
                'progress_hooks': [self.progress_hook],
                'ignoreerrors': True,
                'ffmpeg_location': os.getcwd(),
            }

            if current_tab == "Standard Download":
                fmt = self.opt_format.get()
                quality = self.opt_quality.get()
                if "list=" in url:
                    ydl_opts['outtmpl'] = f'{folder_path}/%(title)s.%(ext)s'

                if fmt == "Audio Only (MP3)":
                    kbps = quality.replace("kbps", "")
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [
                        {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': kbps}]
                else:
                    height = quality.replace("p", "")
                    ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            elif current_tab == "Music Album Maker":
                kbps = self.opt_album_quality.get().replace("kbps", "")
                ydl_opts['outtmpl'] = f'{folder_path}/%(playlist_index)s-%(title)s.%(ext)s'
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': kbps}]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.finish_download(1)

        except Exception as e:
            if "User Cancelled" in str(e):
                self.lbl_status.configure(text="Cancelled", text_color="yellow")
            else:
                self.lbl_status.configure(text=f"Error: Check Console", text_color="red")
                print(e)
            self.finish_download(0)

    def progress_hook(self, d):
        if self.cancel_download == 1: raise Exception("User Cancelled")

        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%', '')
                self.progress_bar.set(float(p) / 100)
                title = d.get('info_dict', {}).get('title', 'Unknown')
                self.lbl_status.configure(text=f"Downloading: {title[:30]}...")
                self.lbl_detail_status.configure(text=f"Speed: {d.get('_speed_str')} | ETA: {d.get('_eta_str')}")
            except:
                pass
        elif d['status'] == 'finished':
            self.lbl_status.configure(text="Processing...", text_color="yellow")

    def finish_download(self, success):
        self.is_downloading = 0
        self.btn_download.configure(state="normal", text="START DOWNLOAD")
        self.btn_stop.configure(state="disabled", fg_color="gray")
        self.progress_bar.set(0)

        if success == 1:
            self.lbl_status.configure(text="Complete!", text_color="green")
            self.lbl_detail_status.configure(text="Files saved successfully.")

            # ACTIVATE BUTTON
            self.btn_open_folder.configure(state="normal", text_color=TEXT_WHITE, border_color=YT_RED)

            if self.tab_view.get() == "Music Album Maker":
                self.batch_tag_files()

    def batch_tag_files(self):
        artist = self.entry_artist.get()
        album = self.entry_album.get()
        year = self.entry_year.get()
        folder = self.final_download_path

        self.lbl_status.configure(text="Tagging & Renaming...", text_color="yellow")

        for filename in os.listdir(folder):
            if filename.endswith(".mp3"):
                try:
                    filepath = os.path.join(folder, filename)
                    # 1. Capture Logic: clean_title_logic now returns "01-SongName"
                    clean_name = self.clean_title_logic(os.path.splitext(filename)[0], artist)

                    # Fix: Ensure single digits get leading zero "1-" -> "01-"
                    if re.match(r'^\d-', clean_name):
                        clean_name = "0" + clean_name

                    # 2. Extract Track Number from the now clean "01-SongName"
                    track_number = ""
                    match_track = re.match(r'^(\d+)-', clean_name)
                    if match_track:
                        track_number = match_track.group(1)

                    try:
                        audio = EasyID3(filepath)
                    except:
                        audio = EasyID3()
                        audio.save(filepath)
                        audio = EasyID3(filepath)

                    if artist: audio['artist'] = artist
                    if album: audio['album'] = album
                    if year: audio['date'] = year
                    if track_number: audio['tracknumber'] = track_number

                    # Title should NOT have "01-" in the tag metadata
                    title_only = re.sub(r'^\d+-', '', clean_name)
                    audio['title'] = title_only
                    audio.save()

                    # Embed Art
                    if self.cover_art_path and os.path.exists(self.cover_art_path):
                        audio_id3 = ID3(filepath)
                        with open(self.cover_art_path, 'rb') as albumart:
                            audio_id3.add(
                                APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=albumart.read()))
                        audio_id3.save()

                    new_path = os.path.join(folder, f"{clean_name}.mp3")
                    if not os.path.exists(new_path):
                        os.rename(filepath, new_path)
                except Exception as e:
                    print(f"Tag Error: {e}")

        self.lbl_status.configure(text="Album Complete!", text_color="green")


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()