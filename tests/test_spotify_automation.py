import json
import os
import unittest.mock
from unittest.mock import Mock

import spotify_automation.spotify_automation as util


class TestSpotifyAutomation(unittest.TestCase):

    def setUp(self) -> None:
        util.USERNAME = 'foo'
        util.CACHE_DIR = '.'

        self.test_file = 'test_file.json'

        with open(self.test_file, 'w') as file_handle:
            file_handle.write(json.dumps([{}, {}, {}], indent=4, default=str))

    def tearDown(self) -> None:
        os.remove(self.test_file)

    def test_get_all_playlists(self):
        """
        Test getting multiple playlists
        """
        session = Mock()

        call_1_results = [{'owner': {'id': 'foo'}} for _ in range(50)]
        call_2_results = [{'owner': {'id': 'foo'}} for _ in range(50)]
        call_3_results = [{'owner': {'id': 'other'}} for _ in range(2)]

        session.user_playlists.side_effect = [
            {'items': call_1_results},
            {'items': call_2_results},
            {'items': call_3_results},
            {'items': []}
        ]

        results = util.get_all_playlists(session)
        self.assertEqual(100, len(results))

    def test_get_playlist_tracks(self):
        """
        Test getting multiple playlist tracks
        """
        session = Mock()

        call_1_results = [{'track': {}} for _ in range(50)]
        call_2_results = [{'track': {}} for _ in range(10)]

        session.playlist_tracks.side_effect = [
            {'items': call_1_results},
            {'items': call_2_results},
            {'items': []}
        ]

        results = util.get_playlist_tracks(session, 'test123')
        self.assertEqual(60, len(results))

    def test_load_tracks_file(self):
        """
        Test loading a test file and checking the items
        """
        results = util.load_tracks_file('test_file')
        self.assertEqual(3, len(results))

    def test_save_tracks_file(self):
        """
        Test saving a test file and then verifying it by reading it
        """
        util.save_tracks_file('test_file', [{}, {}, {}, {}, {}])
        results = util.load_tracks_file('test_file')
        self.assertEqual(5, len(results))
