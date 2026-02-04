"""!
@file app.py
@brief Application entry point.
@details Inherits from the View and instantiates the Logic Controller.
"""

from view import DownloaderView
from logic import DownloaderLogic

class DownloaderApp(DownloaderView):
    """!
    @brief Main Application class.
    @details Combines the View (GUI) and Logic (Controller).
    """

    def __init__(self):
        # 1. Initialize GUI
        super().__init__()

        # 2. Initialize Logic Controller
        self.logic = DownloaderLogic(self)

        # 3. Connect GUI Signals to Logic Slots
        self._connect_signals()

    def _connect_signals(self):
        """!
        @brief Wires up all buttons and inputs to their Logic functions.
        """
        # Header / Inputs
        self.entry_url.bind("<Return>", lambda e: self.logic.load_video_info_thread())
        self.entry_url.bind("<Control-v>", lambda e: self.after(100, self.logic.load_video_info_thread))
        self.btn_paste.configure(command=self.logic.paste_and_load)

        # Standard Tab
        self.opt_format.configure(command=self.logic.update_quality_options)
        self.btn_std_select.configure(command=self.logic.launch_track_editor)

        # Album Tab
        self.btn_cover.configure(command=self.logic.select_cover_art)
        self.btn_edit_tracks.configure(command=self.logic.launch_track_editor)

        # Folder
        self.btn_browse.configure(command=self.logic.browse_folder)

        # Main Actions
        self.btn_download.configure(command=self.logic.start_download_thread)
        self.btn_stop.configure(command=self.logic.stop_download)
        self.btn_open_folder.configure(command=self.logic.open_target_folder)

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()