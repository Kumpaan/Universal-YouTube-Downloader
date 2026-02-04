"""!
@file ui_components.py
@brief Custom UI widgets and dialogs.
@details Contains the TrackEditorDialog for managing playlist content.
"""

import customtkinter as ctk
import os
from settings import YT_BG, YT_SEC, YT_RED, YT_RED_HOVER
from utils import get_bin_path


class TrackEditorDialog(ctk.CTkToplevel):
    """!
    @brief A popup window for editing playlist tracks.
    @details Allows the user to rename tracks and toggle which tracks to download.
    """

    def __init__(self, parent, track_list, callback):
        """!
        @brief Initialize the editor dialog.

        @param parent The parent CTk window.
        @param track_list A list of strings representing video titles.
        @param callback The function to call when "Save" is clicked. Receives (titles, states).
        """
        super().__init__(parent)
        self.callback = callback
        self.title("Edit & Select Tracks")
        self.geometry("650x700")
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

        # --- Header ---
        self.lbl = ctk.CTkLabel(self, text=f"Found {len(track_list)} Tracks", font=("Arial", 20, "bold"))
        self.lbl.pack(pady=10)
        self.lbl_sub = ctk.CTkLabel(self, text="Uncheck items to skip them. Rename items to change tags.",
                                    text_color="gray")
        self.lbl_sub.pack(pady=0)

        # --- Scrollable List ---
        self.scroll = ctk.CTkScrollableFrame(self, width=600, height=550, fg_color=YT_SEC)
        self.scroll.pack(pady=10, padx=10, fill="both", expand=True)

        self.entries = []  # Stores Entry widgets
        self.checks = []  # Stores CheckBox widgets

        for i, title in enumerate(track_list):
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # 1. Checkbox (Download? Yes/No)
            chk_var = ctk.IntVar(value=1)
            chk = ctk.CTkCheckBox(row, text="", variable=chk_var, width=24, checkbox_width=20, checkbox_height=20,
                                  fg_color=YT_RED)
            chk.pack(side="left", padx=(5, 10))
            self.checks.append(chk_var)

            # 2. Number Label
            lbl_num = ctk.CTkLabel(row, text=f"{i + 1}.", width=30, text_color="gray")
            lbl_num.pack(side="left", padx=5)

            # 3. Title Entry (Rename)
            ent = ctk.CTkEntry(row, width=450)
            ent.insert(0, title)
            ent.pack(side="left", fill="x", expand=True)
            self.entries.append(ent)

        # --- Footer ---
        self.btn_save = ctk.CTkButton(self, text="CONFIRM SELECTION", command=self.save_and_close,
                                      fg_color=YT_RED, hover_color=YT_RED_HOVER, height=40, font=("Arial", 12, "bold"))
        self.btn_save.pack(pady=10, padx=20, fill="x")

    def save_and_close(self):
        """!
        @brief Collects data from widgets and triggers the callback.
        @details Returns two lists:
                 1. new_titles: List of strings (renamed titles).
                 2. download_states: List of booleans (1=Download, 0=Skip).
        """
        new_titles = [e.get().strip() for e in self.entries]
        download_states = [c.get() for c in self.checks]

        self.callback(new_titles, download_states)
        self.destroy()