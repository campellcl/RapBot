"""
SpotifyArtistListGenerator.py
Generates a list of artists in a given genre for use in a lookup table when data mining.
"""
__author__ = "Chris Campell"
__version__ = "3/17/2017"

import os
import pprint
from collections import OrderedDict
import operator
import json
import spotipy
from spotipy import util as sputil

def main():
    """
    main -Performs Developer Authorization with the Spotify API.
    :return sp: A Spotipy instance that has successfully completed authorization with Spotify API.
    """
    SPOTIPY_ACCT_USERNAME = 'duckyblarg'
    SPOTIPY_CLIENT_ID = 'd8e6bbe7d2984bf994a9968205fc55d6'
    # Please don't steal and use this key, this account is a dummy account used only for this script:
    SPOTIPY_CLIENT_SECRET = '37258100e7fd459fbcff4ad2bbbeddcc'
    API_REDIRECT_URI = 'https://artistlist/auth/callback/'
    API_AUTH_CALLBACK_URL = 'https://artistlist/auth/callback/?code=AQBPOiTUjtiA5AkIQoXRmKzdZeZxaSMTc1jr2DFWulGeAL0eZy1fhsfQen1Aq2Zdvi6WfJ48GjlGQjdIZu5_TWVojw69utnW_7ATFsQ8ae25VGF08fyZND9a7bEA3C7W2ivfL2jJBWNWBPRLZwukcpE-T6s2miskEWgCyPNXdlJnoZL4KVKYJeFO3JpQUekq0jVmAAIgamH7yS-YkjfZAf5ik3RFmt7r1AQYqp6TklEOlDFF'
    # Declare Scopes for Access Requests:
    scope = 'playlist-read-collaborative'
    # Attempt to Perform Authorization:
    auth_token = sputil.prompt_for_user_token(
        username=SPOTIPY_ACCT_USERNAME, client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=API_REDIRECT_URI, scope=scope)
    sp = None
    # Check to see if Authentication Success:
    if auth_token:
        sp = spotipy.Spotify(auth=auth_token)
        print("Developer Authorization Successful")
        return sp
    else:
        print("Can't get token for %s" % SPOTIPY_ACCT_USERNAME)
        exit(-1)

def get_hip_hop_classics_tracks(username, spotipy_instance, hip_hop_tracks):
    """
    get_hip_hop_classics_tracks -Returns the provided 'hip_hop_tracks' container with added entries from the public
        playlist 'Hip Hop Classics'.
    :param username: The developer account username.
    :param spotipy_instance: A Spotipy instance that has successfully completed authorization with Spotify API.
    :param hip_hop_tracks: Storage structure for retrieved track information.
    :return hip_hop_tracks: The provided structure with added track entries from the 'Hip Hop Classics' playlist.
    """
    # Attempt to retrieve list of songs in the 'HipHop Classics' Playlist
    playlists = spotipy_instance.user_playlists(user=username)
    # Get the Hip-Hop Classics Playlist:
    for playlist in playlists['items']:
        if playlist['id'] == '1cUJDDYTSqd5LTuImKdrlJ':
            owner = 'sonymusicthelegacy'
            results = spotipy_instance.user_playlist(user=owner, playlist_id=playlist['id'], fields='tracks,next')
            tracks = results['tracks']
            for track_container in tracks['items']:
                track = track_container['track']
                track_name = track['name']
                track_album = track['album']['name']
                track_pop = track['popularity']
                # Grab every artist on the track:
                track_artists = []
                for artist in track['artists']:
                    track_artists.append(artist['name'])
                # Append the track if not already in storage structure:
                if track_name not in hip_hop_tracks:
                    hip_hop_tracks[track_name] = {
                        'name': track_name, 'album': track_album,
                        'popularity': int(track_pop), 'artists': track_artists
                    }
    return hip_hop_tracks

def reassign_keys_as_unique_id(hip_hop_tracks):
    """
    reassign_keys_as_unique_id -Takes a 'hip_hop_tracks' dictionary and re-writes it so that each entry has a unique
        identifier as its key instead of the song name. The track_name key is retained as a value in the new dictionary.
    :param hip_hop_tracks: A populated dictionary of hip-hop tracks.
    :return rap_tracks: A dictionary identical to the provided 'hip_hop_tracks' except with unique identifiers as keys.
    """
    rap_tracks = {}
    for track_name, value in hip_hop_tracks.items():
        track_info = value
        track_info['name'] = track_name
        rap_tracks[len(rap_tracks)] = track_info
    return rap_tracks

def sort_tracks_by_popularity(hip_hop_tracks):
    """
    sort_tracks_by_popularity -Returns an ordered dictionary based on track popularity.
    :param hip_hop_tracks: A populated dictionary of hip-hop tracks.
    :return rap_tracks: A value-identical dictionary to the provided 'hip_hop_tracks' with the exception that tracks are
        sorted in descending order of popularity and assigned new keys/ids to reflect this ordering.
    """
    # Efficient sorting method from http://stackoverflow.com/questions/13781981/lambda-function-in-sorted-dictionary-list-comprehension
    rap_tracks = OrderedDict()
    for track_id, track_info in sorted(hip_hop_tracks.items(), key=lambda hip_hop_track: hip_hop_track[1]['popularity'], reverse=True):
        rap_tracks[len(rap_tracks)] = track_info
    return rap_tracks

if __name__ == '__main__':
    # Get file path to the desired storage directory:
    write_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Data/Spotify'))
    sp = main()
    print("Building Track List...")
    hip_hop_tracks = {}
    hip_hop_tracks = get_hip_hop_classics_tracks(username='duckyblarg', spotipy_instance=sp, hip_hop_tracks=hip_hop_tracks)
    hip_hop_tracks = reassign_keys_as_unique_id(hip_hop_tracks)
    print("Done!\nSorting Track List by Popularity...")
    hip_hop_tracks = sort_tracks_by_popularity(hip_hop_tracks)
    print("Done!\nWriting Track List...")
    with open(write_path + '/HipHopTracks.json', 'w') as fp:
        json.dump(hip_hop_tracks, fp)
    print("Done!\nBuilding Artist List...")
    rap_artists_sorted_by_pop = OrderedDict()
    for track_id, track_info in hip_hop_tracks.items():
        # print("Track: %s\tPop: %d\tArtist: %s" %(track_info['name'], track_info['popularity'], track_info['artists'][0]))
        print("Artist: %s\t\t\t\tPopularity: %d" %(track_info['artists'][0], track_info['popularity']))

