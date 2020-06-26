import json
import logging
import os

import spotipy
from spotipy import SpotifyOAuth, Spotify

logging.getLogger().setLevel('INFO')
USERNAME = os.environ.get('USERNAME')
CACHE_DIR = os.environ.get('spotify_cache')
MAX_PLAYLIST_TRACKS = 11000


def login() -> Spotify:
    """
    Attempt to log in to Spotify as the current user
    These OS Env variables must be set:
        SPOTIPY_CLIENT_ID
        SPOTIPY_CLIENT_SECRET
        SPOTIPY_REDIRECT_URI
    """
    logging.info("Attempting to login...")

    scope = 'user-library-read ' \
            'playlist-read-private ' \
            'playlist-modify-private ' \
            'playlist-modify-public ' \
            'user-library-modify ' \
            'user-read-recently-played'

    session = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    logging.info(f"Successfully logged in as: {USERNAME}")
    return session


def get_all_playlists(session: Spotify) -> list:
    """
    Call Spotify API to get a list of playlists for the user

    :param session:     Spotipy session
    :return:            List of dictionaries, each is a playlist
    """
    logging.info("Retrieving list of playlists from Spotify...")
    all_playlists = []

    for playlist_offset in range(0, 10000, 50):
        playlists = session.user_playlists(USERNAME, limit=50, offset=playlist_offset)

        if len(playlists['items']) < 1:
            break

        [all_playlists.append(p) for p in playlists['items'] if p['owner']['id'] == USERNAME]

    logging.info(f'Retrieved {len(all_playlists)} playlists')
    return all_playlists


def get_playlist_tracks(session: Spotify, playlist_id: str) -> list:
    """
    Get the list of tracks in a playlist
    The most tracks you can query at once is 100 so you must iterate and use an offset

    :param session:             Spotipy session
    :param playlist_id:         Playlist ID to get tracks
    :return:                    List of track dictionaries
    """
    tracks_in_playlist = []
    for track_offset in range(0, MAX_PLAYLIST_TRACKS, 100):

        results = session.playlist_tracks(USERNAME, playlist_id, limit=100, offset=track_offset)
        if len(results['items']) < 1:
            break

        [tracks_in_playlist.append(item['track']) for item in results['items']]

    return tracks_in_playlist


def load_tracks_file(playlist_name: str) -> list:
    """
    Load the tracks from a local cache json file

    :param playlist_name:       Name of the playlist to load the tracks from
    :return:                    List of track dictionaries
    """
    file_name = os.path.join(CACHE_DIR, playlist_name + '.json')
    logging.info('Loading playlists tracks from file: "{}"'.format(file_name))
    try:
        with open(file_name, 'r') as file_handle:
            return json.loads(file_handle.read())
    except FileNotFoundError:
        return []


def save_tracks_file(playlist_name, playlist_tracks) -> None:
    """
    Write a list of playlist tracks to a json file

    :param playlist_name: Name of playlist to save
    :param playlist_tracks: List of track dictionaries
    """
    file_name = os.path.join(CACHE_DIR, playlist_name + '.json')
    logging.info('Saving playlists tracks to file: "{}"'.format(file_name))
    with open(file_name, 'w') as file_handle:
        file_handle.write(json.dumps(playlist_tracks, indent=4, default=str))

    logging.info(f'Saved {len(playlist_tracks)} tracks to {file_name}')
