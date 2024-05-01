import logging

import spotify_automation.spotify_automation as util

logging.getLogger().setLevel('INFO')

session = util.login()
playlists = util.get_all_playlists(session)
util.update_local_cache(session, playlists)

for playlist in playlists:
    logging.info(f"Processing playlist: {playlist['name']}")
    util.process_queue_playlist(session, playlist)
    util.find_possible_duplicate_tracks(playlist)
