import logging

import spotify_automation.spotify_automation as util

logging.getLogger().setLevel('INFO')

session = util.login()
playlists = util.get_all_playlists(session)
