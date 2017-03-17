"""
SpotifyArtistListGenerator.py
Generates a list of artists in a given genre for use in a lookup table when data mining.
"""
__author__ = "Chris Campell"
__version__ = "3/17/2017"

import os
import json
import spotipy
from spotipy import util as sputil

def main():
    SPOTIPY_ACCT_USERNAME = 'duckyblarg'
    SPOTIPY_CLIENT_ID = 'd8e6bbe7d2984bf994a9968205fc55d6'
    # Please don't steal and use this key, this account is a dummy account used only for this script:
    SPOTIPY_CLIENT_SECRET = '37258100e7fd459fbcff4ad2bbbeddcc'
    API_REDIRECT_URI = 'https://artistlist/auth/callback/'
    API_AUTH_CALLBACK_URL = 'https://artistlist/auth/callback/?code=AQBr9QT92DRaxH88hIYrx9LJwd6a_kWLkl0DW8Wnj2v5AvELpGIBdN1tVV1Y7FuIwXim80zKGQE4rodXTqK4QgJ6smrx1Jf6QvES00NwdLuEus4xlZg-Q_uSTvt2YxiduIS9b1sjXqsNYNw3AOhFOo7ubtBG-hh-pRsI_BA6IeKtLVA_YPRT3sSxWwLpBxSMGqcdLIlLDA'
    # Attempt to Perform Authorization:
    auth_token = sputil.prompt_for_user_token(
        username=SPOTIPY_ACCT_USERNAME, client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=API_REDIRECT_URI)
    # Check to see if Authentication Success:
    if auth_token:
        sp = spotipy.Spotify(auth=auth_token)
        print("Developer Authorization Successful")
    else:
        print("Can't get token for %s" % SPOTIPY_ACCT_USERNAME)


if __name__ == '__main__':
    # Get file path to the desired storage directory:
    write_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Data/Spotify'))
    main()
