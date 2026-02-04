import customtkinter as ctk
import os
from settings import YT_BG, YT_SEC, YT_RED, YT_RED_HOVER
from utils import get_bin_path

class TrackEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, track_list, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Edit Album Tracklist")
        self.geometry("600x700")
        self.configure(fg_color=YT_BG)
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()

        # Set icon (Windows only)
        if os.name == 'nt':
            try:
                self.after(200, lambda: self.iconbitmap(get_bin_path("icon.ico")))
            except:
                pass

        # Title
        self.lbl = ctk.CTkLabel(self, text=f"Edit {len(track_list)} Tracks", font=("Arial", 20, "bold"))
        self.lbl.pack(pady=10)
        self.lbl_sub = ctk.CTkLabel(self, text="These names will be used for Filenames and Tags.", text_color="gray")
        self.lbl_sub.pack(pady=0)

        # Scrollable Area
        self.scroll = ctk.CTkScrollableFrame(self, width=550, height=550, fg_color=YT_SEC)
        self.scroll.pack(pady=10, padx=10, fill="both", expand=True)

        self.entries = []

        for i, title in enumerate(track_list):
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            lbl_num = ctk.CTkLabel(row, text=f"{i + 1}.", width=30, text_color="gray")
            lbl_num.pack(side="left", padx=5)

            ent = ctk.CTkEntry(row, width=450)
            ent.insert(0, title)
            ent.pack(side="left", fill="x", expand=True)

            self.entries.append(ent)

        self.btn_save = ctk.CTkButton(self, text="SAVE CHANGES", command=self.save_and_close,
                                      fg_color=YT_RED, hover_color=YT_RED_HOVER, height=40)
        self.btn_save.pack(pady=10, padx=20, fill="x")

    def save_and_close(self):
        new_list = [e.get().strip() for e in self.entries]
        self.callback(new_list)
        self.destroy()