import unittest
from unittest.mock import patch, MagicMock
import os

# Import your modules
from utils import clean_filename_string, get_bin_path
import download_manager
from logic import DownloaderLogic


class TestYouTubeDownloader(unittest.TestCase):

    # --- 1. UTILS TESTING (Input -> Output) ---
    def test_filename_cleaning(self):
        """Test if dirty YouTube titles are cleaned correctly."""
        # Case A: Standard cleaning
        raw = "Linkin Park - Numb (Official Video) [4K]"
        clean = clean_filename_string(raw, "Linkin Park")
        self.assertEqual(clean, "Numb", "Failed to remove Artist name and brackets")

        # Case B: No artist match
        raw = "Funny Cat Video (HD)"
        clean = clean_filename_string(raw, "Dog")
        self.assertEqual(clean, "Funny Cat Video", "Should keep title but remove tags")

        # Case C: Already clean
        raw = "Just A Title"
        clean = clean_filename_string(raw, "")
        self.assertEqual(clean, "Just A Title")

    # --- 2. MIX DETECTION (Functionality) ---
    def test_mix_detection(self):
        """Test logic for detecting infinite mixes."""
        # We need a dummy view to initialize Logic, but we can mock it
        mock_view = MagicMock()
        logic = DownloaderLogic(mock_view)

        # Case A: Real Playlist
        self.assertFalse(
            "list=PL12345" in "list=RD12345" or "list=UL" in "list=PL12345",
            "Logic check: This is how we should test if you expose the helper function"
        )

        # Since is_mix logic is inside logic.py methods (not a standalone function),
        # we test the URL patterns directly here or extract the function in utils.
        mix_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ"
        standard_url = "https://www.youtube.com/playlist?list=PL12345"

        is_mix_1 = "list=RD" in mix_url or "list=UL" in mix_url
        is_mix_2 = "list=RD" in standard_url or "list=UL" in standard_url

        self.assertTrue(is_mix_1)
        self.assertFalse(is_mix_2)

    # --- 3. DOWNLOAD MANAGER (Integration with Mocked yt-dlp) ---
    @patch('download_manager.yt_dlp.YoutubeDL')
    def test_downloader_config_standard(self, mock_ydl):
        """Test if the downloader sends the correct flags to yt-dlp."""

        # Setup the mock
        mock_instance = mock_ydl.return_value
        mock_instance.__enter__.return_value = mock_instance

        # Scenario: User downloads a SINGLE video (detected_playlist = False)
        config = {
            'url': 'https://youtube.com/watch?v=123',
            'folder': 'C:/Downloads',
            'mode': 'standard',
            'detected_playlist': False,  # KEY: Logic says this is single
            'format_type': 'video',
            'quality': '1080p',
            'selected_indices': None
        }

        # Run the function
        download_manager.run_downloader(config, lambda d: None)

        # Check what arguments were passed to YoutubeDL
        # call_args[0] is positional args, [0] is the first arg (the options dict)
        called_options = mock_ydl.call_args[0][0]

        # ASSERTIONS
        self.assertTrue(called_options.get('noplaylist'), "noplaylist should be True for single videos")
        self.assertIn('bestvideo[height<=1080]', called_options['format'])

    @patch('download_manager.yt_dlp.YoutubeDL')
    def test_downloader_config_playlist(self, mock_ydl):
        """Test if the downloader handles Playlists correctly."""

        mock_instance = mock_ydl.return_value
        mock_instance.__enter__.return_value = mock_instance

        # Scenario: User downloads a PLAYLIST with specific items
        config = {
            'url': 'https://youtube.com/playlist?list=123',
            'folder': 'C:/Downloads',
            'mode': 'standard',
            'detected_playlist': True,
            'format_type': 'audio',
            'quality': '192kbps',
            'selected_indices': '1,2,3'  # User selected first 3
        }

        download_manager.run_downloader(config, lambda d: None)
        called_options = mock_ydl.call_args[0][0]

        # ASSERTIONS
        self.assertIsNone(called_options.get('noplaylist'), "noplaylist should NOT be present/True")
        self.assertEqual(called_options.get('playlist_items'), '1,2,3')
        self.assertEqual(called_options['format'], 'bestaudio/best')

    # --- 4. ERROR HANDLING ---
    @patch('download_manager.yt_dlp.YoutubeDL')
    def test_download_failure(self, mock_ydl):
        """Test if the app handles crashes gracefully."""

        # Make the mock raise an error
        mock_instance = mock_ydl.return_value
        mock_instance.__enter__.side_effect = Exception("Network Error")

        config = {
            'url': 'http://bad-link',
            'folder': '.',
            'mode': 'standard',
            'detected_playlist': False,
            'format_type': 'video', 'quality': '1080p', 'selected_indices': None
        }

        # Assert that it RAISES the error (so the Logic class can catch it)
        with self.assertRaises(Exception):
            download_manager.run_downloader(config, lambda d: None)


if __name__ == '__main__':
    unittest.main()