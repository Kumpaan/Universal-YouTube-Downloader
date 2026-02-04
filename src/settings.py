"""!
@file settings.py
@brief Global configuration and constants for the application.
@details Contains theme settings, color palettes, and application constants used across modules.
"""

import customtkinter as ctk

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- Constants ---
## @var APP_TITLE
# The window title displayed in the OS window manager.
APP_TITLE = "Universal YouTube Downloader v0.3.0"

## @var APP_SIZE
# The initial dimensions of the application window.
APP_SIZE = "700x820"

## @var APP_ID
# Specific AppUserModelID for Windows Taskbar grouping.
APP_ID = 'kumpaan.youtubedownloader.v0.3.0'

# --- Colors ---
## @var YT_BG
# Background color (Pitch Black).
YT_BG = "#0f0f0f"

## @var YT_SEC
# Secondary background color (Dark Gray).
YT_SEC = "#272727"

## @var YT_RED
# Primary accent color (YouTube Red).
YT_RED = "#CC0000"

## @var YT_RED_HOVER
# Hover state color for primary buttons.
YT_RED_HOVER = "#990000"

## @var TEXT_WHITE
# Standard text color.
TEXT_WHITE = "#FFFFFF"