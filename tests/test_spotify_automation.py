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

        session.user_playlist_tracks.side_effect = [
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

    def test_update_local_cache(self):
        """
        Test updating the local cache using the test file
        """
        session = Mock()
        playlists = [
            {
                'name': 'test_file',
                'id': '12345',
                'tracks': {'total': 100}
            }
        ]

        call_1_results = [{'track': {}} for _ in range(50)]
        call_2_results = [{'track': {}} for _ in range(20)]

        session.user_playlist_tracks.side_effect = [
            {'items': call_1_results},
            {'items': call_2_results},
            {'items': []}
        ]
        util.update_local_cache(session, playlists)
        results = util.load_tracks_file('test_file')
        self.assertEqual(70, len(results))

    def test_create_track_hash(self):
        """
        Test creating a hash map of tracks
        """
        result = util.create_track_hash([{'id': '123'}, {'id': '456'}])
        self.assertEqual({
            '123': {'id': '123'},
            '456': {'id': '456'}
        }, result)

    def test_load_all_disliked_tracks(self):
        """
        Test loading a list of "disliked" tracks
        """
        util.save_tracks_file('disliked_14', [{'id': '123'}, {'id': '456'}, {'id': '789'}])
        util.save_tracks_file('disliked_23', [{'id': '987'}, {'id': '654'}, {'id': '321'}])
        playlists = [
            {'name': 'disliked_14'},
            {'name': 'disliked_23'}
        ]
        results = util.load_all_disliked_tracks(playlists)
        os.remove('disliked_14.json')
        os.remove('disliked_23.json')
        self.assertEqual({
            '123': {'id': '123'},
            '456': {'id': '456'},
            '789': {'id': '789'},
            '987': {'id': '987'},
            '654': {'id': '654'},
            '321': {'id': '321'}
        }, results)

    def test_scan_playlist_for_disliked_tracks(self):
        """
        Test removing 2 disliked tracks from the test playlist. Track ID 789 should remain.
        """
        session = Mock()
        session.user_playlist_remove_all_occurrences_of_tracks.return_value = None

        disliked = {
            '123': {'id': '123'},
            '456': {'id': '456'}
        }

        playlist = {
            'name': 'Foo Playlist',
            'id': '123456789'
        }

        playlist_tracks = [
            {'id': '123', 'name': 'Track1', 'uri': '1', 'artists': [{'name': 'Foo Artist 1'}]},
            {'id': '456', 'name': 'Track2', 'uri': '1', 'artists': [{'name': 'Foo Artist 2'}]},
            {'id': '789', 'name': 'Track3', 'uri': '1', 'artists': [{'name': 'Foo Artist 3'}]},
        ]

        util.save_tracks_file('Foo Playlist', playlist_tracks)

        util.scan_playlist_for_disliked_tracks(session, playlist, disliked)
        os.remove('Foo Playlist.json')
        self.assertEqual(2, session.user_playlist_remove_all_occurrences_of_tracks.call_count)

    def test_process_queue_playlist(self):
        """
        Test removing 2 disliked tracks from the test playlist. Track ID 789 should remain.
        """
        session = Mock()
        session.user_playlist_remove_all_occurrences_of_tracks.return_value = None

        queue_playlist = {
            'name': 'Foo Playlist Queue',
            'id': '123456789'
        }

        queue_playlist_tracks = [
            {'id': '123', 'name': 'Track1', 'uri': '1', 'artists': [{'name': 'Foo Artist 1'}]},
            {'id': '456', 'name': 'Track2', 'uri': '1', 'artists': [{'name': 'Foo Artist 2'}]},
            {'id': '789', 'name': 'Track3', 'uri': '1', 'artists': [{'name': 'Foo Artist 3'}]},
        ]
        util.save_tracks_file('Foo Playlist Queue', queue_playlist_tracks)

        destination_playlist_tracks = [
            {'id': '456', 'name': 'Track2', 'uri': '1', 'artists': [{'name': 'Foo Artist 2'}]},
            {'id': '789', 'name': 'Track3', 'uri': '1', 'artists': [{'name': 'Foo Artist 3'}]},
        ]
        util.save_tracks_file('Foo Playlist', destination_playlist_tracks)

        util.process_queue_playlist(session, queue_playlist)
        os.remove('Foo Playlist Queue.json')
        os.remove('Foo Playlist.json')
        self.assertEqual(2, session.user_playlist_remove_all_occurrences_of_tracks.call_count)

    def test_find_possible_duplicate_tracks_matching_string(self):
        """
        Test finding a duplicate track, with two tracks difference in duration less than 10 seconds
        """
        playlist_tracks = [
            {'id': '1', 'name': 'Track3', 'duration_ms': 10000, 'artists': [{'name': 'Foo 3'}]},
            {'id': '2', 'name': 'Track3', 'duration_ms': 10001, 'artists': [{'name': 'Foo 3'}]},
        ]
        util.save_tracks_file('test_playlist', playlist_tracks)
        result = util.find_possible_duplicate_tracks({'name': 'test_playlist'})
        self.assertEqual(['2'], result)
        os.remove('test_playlist.json')

    def test_find_possible_duplicate_tracks_different_duration(self):
        """
        Test finding a duplicate track, with two tracks difference in duration more than 10 seconds
        """
        playlist_tracks = [
            {'id': '1', 'name': 'Track3', 'duration_ms': 10000, 'artists': [{'name': 'Foo 3'}]},
            {'id': '2', 'name': 'Track3', 'duration_ms': 20001, 'artists': [{'name': 'Foo 3'}]},
        ]
        util.save_tracks_file('test_playlist', playlist_tracks)
        result = util.find_possible_duplicate_tracks({'name': 'test_playlist'})
        self.assertEqual([], result)
        os.remove('test_playlist.json')
