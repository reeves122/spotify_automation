import unittest.mock
from unittest.mock import Mock

import spotify_automation.spotify_automation as util


class TestSpotifyAutomation(unittest.TestCase):

    def test_get_all_playlists(self):
        util.USERNAME = 'foo'
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