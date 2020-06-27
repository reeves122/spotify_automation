import logging

import spotify_automation.spotify_automation as util

logging.getLogger().setLevel('INFO')

session = util.login()
playlists = util.get_all_playlists(session)
util.update_local_cache(session, playlists)
disliked_tracks = util.load_all_disliked_tracks(playlists)

for playlist in playlists:
    logging.info(f"Processing playlist: {playlist['name']}")
    util.scan_playlist_for_disliked_tracks(session, playlist, disliked_tracks)
    util.process_queue_playlist(session, playlist)
