"""
SpotifyTrackListGenerator.py
Generates a list of top ten tracks for each artist in the ManualArtistList.csv inputfile.
"""
__author__ = "Chris Campell"
__version__ = "3/19/2017"

import os
import spotipy
from spotipy import util as sputil
import pandas as pd
from collections import OrderedDict
import json

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
        print("Developer Authorization Successful.")
        return sp
    else:
        print("Can't get token for %s" % SPOTIPY_ACCT_USERNAME)
        exit(-1)

def read_artists(input_file_path):
    """
    read_artists -Reads the ManualArtistList.csv file into memory, obtaining each artist's:
        1. internal identifier -used by this script.
        2. Spotify URI / Identifier -Used by Spotify's REST API to retrieve artist's track list.
        3. Name -The string representation of the artist's name.
    :param input_file_path: The file path to the ManualArtistList.csv file.
    :return hip_hop_artists: A container dictionary containing the above information
        about each artist in the targeted csv.
    """
    hip_hop_artists = {}
    artist_csv = pd.read_csv(input_file_path + "/ManualArtistList.csv")
    for col in artist_csv:
        for row_index, row_entry in enumerate(artist_csv[col]):
            if col == 'artist':
                if row_entry not in hip_hop_artists.keys():
                    hip_hop_artists[row_index] = {"name": row_entry, 'id': row_index, 'uri': None}
                else:
                    print("Duplicate Artist at Row Index: %d, Artist: %s" %(row_index, row_entry))
            if col == 'uri':
                hip_hop_artists[row_index]['uri'] = str.split(row_entry, sep=':')[2]
    return hip_hop_artists

def get_artists_top_ten_tracks(hip_hop_artists):
    """
    get_artists_top_ten_tracks -Populates every artist in the provided dictionary with their top ten tracks according
        to the Spotify API.
    :param hip_hop_artists: The dictionary of hip hop artists with associated URI's.
    :return hip_hop_tracks: The list of unique tracks associated with each artist and their popularity.
    """
    hip_hop_tracks = {}
    for artist_id, artist_info in hip_hop_artists.items():
        artist_name = artist_info['name']
        lazy_uri = 'spotify:artist:' + artist_info['uri']
        sp_top_tracks = sp.artist_top_tracks(artist_id=lazy_uri, country='US')
        for track in sp_top_tracks['tracks'][:10]:
            if track['uri'] not in hip_hop_tracks:
                hip_hop_tracks[len(hip_hop_tracks)] = {
                    'name': track['name'], 'uri': track['uri'],
                    'popularity': track['popularity'], 'artist': {
                        'name': artist_name, 'uri': artist_info['uri']
                    }
                }
            else:
                print("Duplicate Track [%s] not added for Artist [%s]." % (track['name'], artist_name))
    return hip_hop_tracks

def assign_artist_popularity_score(hip_hop_tracks):
    pass

def sort_tracks_by_popularity(hip_hop_tracks):
    """
    sort_tracks_by_popularity -Returns an identical instance to the provided hip_hop_tracks dictionary, except the new
        instance is sorted by popularity in descending order.
    :param hip_hop_tracks: The input list of hip-hop-tracks and their associated popularity scores and artists.
    :return sorted_tracks: The provided list of hip-hop tracks now sorted in descending order by popularity.
    """
    sorted_tracks = OrderedDict()
    # Efficient sorting method from:
    #   http://stackoverflow.com/questions/13781981/lambda-function-in-sorted-dictionary-list-comprehension
    for track_id, track_info in sorted(hip_hop_tracks.items(),
                                       key=lambda hip_hop_track: hip_hop_track[1]['popularity'], reverse=True):
        sorted_tracks[len(sorted_tracks)] = track_info
    return sorted_tracks

if __name__ == '__main__':
    write_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../../Data/ArtistLookupTables/Spotify'))
    input_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../../Data/ArtistLookupTables/GooglePlay'))
    hip_hop_tracks = {}
    # Authenticate using Spotipy
    sp = main()
    # Read in every desired artist to have top tracks recorded for:
    hip_hop_artists = read_artists(input_file_path)
    # Get artist top-ten tracks
    hip_hop_tracks = get_artists_top_ten_tracks(hip_hop_artists=hip_hop_artists)
    # hip_hop_tracks = assign_artist_popularity_score(hip_hop_tracks)
    sorted_by_pop_tracks = sort_tracks_by_popularity(hip_hop_tracks)
    # log output in json format:
    with open(write_path + '/SortedTrackLookupTable.json', 'w') as fp:
        json.dump(sorted_by_pop_tracks, fp=fp)
        print("Write successful; data saved.")
