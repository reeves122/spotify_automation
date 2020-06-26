import json
import logging
import os
import sys

import spotipy
from spotipy import SpotifyOAuth

logging.getLogger().setLevel('INFO')
USERNAME = os.environ.get('USERNAME')


def login():
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
