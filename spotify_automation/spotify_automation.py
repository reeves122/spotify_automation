import json
import logging
from math import isclose
import os
import sys

import spotipy
from spotipy import SpotifyOAuth, Spotify

logging.getLogger().setLevel('INFO')
USERNAME = os.environ.get('USERNAME')
CACHE_DIR = os.environ.get('CACHE_DIR', '.spotify_cache')
RESPONSE_URL = os.environ.get('RESPONSE_URL')
MAX_PLAYLIST_TRACKS = 11000


def login() -> Spotify:
    """
    Attempt to log in to Spotify as the current user
    These OS Env variables must be set:
        SPOTIPY_CLIENT_ID
        SPOTIPY_CLIENT_SECRET
        SPOTIPY_REDIRECT_URI

    :return:                Spotify session
    """
    scope = 'user-library-read ' \
            'playlist-read-private ' \
            'playlist-modify-private ' \
            'playlist-modify-public ' \
            'user-library-modify ' \
            'user-read-recently-played'

    auth = SpotifyOAuth(scope=scope, username=USERNAME,
                        cache_path=os.path.join(CACHE_DIR, 'auth_token.json'))

    token_info = auth.get_cached_token()
    if token_info:
        logging.info('Using cached token for login')
        return _get_login_session(token_info['access_token'])

    code = auth.parse_response_code(RESPONSE_URL)
    if code:
        logging.info('Found response URL. Getting an access token...')
        token_info = auth.get_access_token(code)
        return _get_login_session(token_info['access_token'])

    logging.warning('Access token not found. Please use the below URL to authorize this '
                    'application and then set the RESPONSE_URL env variable to the URL '
                    'spotify responds with and run this application again')
    logging.warning(auth.get_authorize_url())
    sys.exit(0)


def _get_login_session(access_token: str) -> Spotify:
    """
    Use an access token to login as a user and set up a session

    :param access_token:    Access token used to login
    :return:                Spotify session
    """
    logging.info("Attempting to login...")
    session = spotipy.Spotify(access_token)
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
        playlists = session.user_playlists(user=USERNAME, limit=50, offset=playlist_offset)

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

        results = session.user_playlist_tracks(USERNAME, playlist_id,
                                               limit=100, offset=track_offset)
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
    logging.debug('Loading playlists tracks from file: "{}"'.format(file_name))
    try:
        with open(file_name, 'r') as file_handle:
            return json.loads(file_handle.read())
    except FileNotFoundError:
        return []


def save_tracks_file(playlist_name, playlist_tracks) -> None:
    """
    Write a list of playlist tracks to a json file

    :param playlist_name:       Name of playlist to save
    :param playlist_tracks:     List of track dictionaries
    """
    file_name = os.path.join(CACHE_DIR, playlist_name + '.json')
    logging.info('Saving playlists tracks to file: "{}"'.format(file_name))
    with open(file_name, 'w') as file_handle:
        file_handle.write(json.dumps(playlist_tracks, indent=4, default=str))

    logging.info(f'Saved {len(playlist_tracks)} tracks to {file_name}')


def update_local_cache(session: Spotify, all_playlists: list) -> None:
    """
    Compare the local track cache files with Spotify and update the local cache as necessary.
    For lack of a better option, the size comparison of the playlist is used to detect changes.

    :param session:             Spotipy session
    :param all_playlists        List of playlist definitions
    """
    logging.info('Updating local cache of playlists...')
    for playlist in all_playlists:
        cache_tracks = load_tracks_file(playlist['name'])

        if len(cache_tracks) == playlist['tracks']['total']:
            continue

        logging.info(f"Detected changes in playlist {playlist['name']}'. Updating local cache.")

        save_tracks_file(playlist['name'], get_playlist_tracks(session, playlist['id']))


def create_track_hash(track_list: list) -> dict:
    """
    Create a dict hash map of tracks by track id to enable fast lookups

    :param track_list:      List of track dictionary items
    """
    return {track['id']: track for track in track_list}


def load_all_disliked_tracks(playlists: list) -> dict:
    """
    Load all the tracks from all the "disliked" playlists to create a single, large list

    :param playlists        List of playlist definitions
    """
    logging.info('Loading disliked tracks...')

    # Load all disliked tracks into a list
    disliked_tracks = []
    [disliked_tracks.extend(load_tracks_file(playlist['name']))
     for playlist in playlists if playlist['name'].startswith('disliked_')]

    logging.info('Loaded {} disliked tracks'.format(len(disliked_tracks)))

    # Convert list to a hash map by track ID
    return create_track_hash(disliked_tracks)


def scan_playlist_for_disliked_tracks(session: Spotify, playlist: dict,
                                      disliked_tracks_hash: dict) -> None:
    """
    Scan the specified playlist for tracks which are in the disliked list and remove them
    from the playlist

    :param session:                     Spotipy session
    :param playlist:                    Playlist definition which will be loaded to scan
    :param disliked_tracks_hash:        Dict hash of disliked tracks
    """
    if playlist['name'].startswith('disliked_'):
        return

    logging.debug('Scanning for disliked tracks in playlist "{}"'.format(playlist['name']))

    for track in load_tracks_file(playlist['name']):

        if disliked_tracks_hash.get(track['id']):
            logging.info('Disliked track found: Artist:"{}" Name:"{}" URI:"{}"'.format(
                track['artists'][0]['name'], track['name'], track['uri']))

            session.user_playlist_remove_all_occurrences_of_tracks(
                USERNAME, playlist['id'], [track['id']])


def process_queue_playlist(session, playlist):
    """
    Scan a "Queue" playlist (playlist of songs yet to be listened to and rated) for songs
    which have been added to the corresponding non-queue playlist. For example, the user may
    have "Favorites" and "Favorites Queue" playlists. The latter being songs the user has not
    heard and rated before. If the user likes a song, they add it to the "Favorites" list and this
    function will then remove it from the "Favorites Queue" playlist.

    :param session:                     Spotipy session
    :param playlist:                    Playlist definition which will be loaded to scan
    """
    if not playlist['name'].endswith(' Queue'):
        return

    logging.debug('Scanning queue playlist "{}"'.format(playlist['name']))

    destination_playlist_track_hash = create_track_hash(
        load_tracks_file(playlist['name'].replace(' Queue', '')))

    for track in load_tracks_file(playlist['name']):

        if destination_playlist_track_hash.get(track['id']):
            logging.info('Track found in destination: Artist:"{}" Name:"{}" URI:"{}"'.format(
                track['artists'][0]['name'], track['name'], track['uri']))

            session.user_playlist_remove_all_occurrences_of_tracks(
                USERNAME, playlist['id'], [track['id']])


def find_possible_duplicate_tracks(playlist):
    """
    Scan the playlist for possible duplicate tracks

    :param playlist:        Playlist definition which will be loaded to scan
    """
    if playlist['name'].startswith('disliked_'):
        return

    deduplicated = {}
    possible_duplicates = set()

    # Try to deduplicate using a string of the track details
    for track in load_tracks_file(playlist['name']):

        unique_key = f"{track['name']} - {track['artists'][0]['name']}"
        unique_key = unique_key.lower()

        if not deduplicated.get(unique_key):
            deduplicated[unique_key] = track
            continue

        # Check if the two track durations are within 10 seconds of each other
        if isclose(deduplicated[unique_key]['duration_ms'], track['duration_ms'], abs_tol=10000):
            logging.warning('Possible duplicate in playlist (by name and artist): '
                            '{} - {}'.format(track['artists'][0]['name'], track['name']))
            possible_duplicates.add(track['id'])

    return list(possible_duplicates)
