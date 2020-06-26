import json
import logging
import os
import sys

import spotipy
from spotipy import SpotifyOAuth, Spotify

logging.getLogger().setLevel('INFO')
USERNAME = os.environ.get('USERNAME')


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
    :return: List of dictionaries, each is a playlist
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
