"""
WebScraper.py
Performs retrieval of plaintext song lyrics from The Online Hip Hop Lyrics Archive (OHLA).
Utilizes the SortedTrackLookupTable.json file to determine the artists to target.
"""
import json
import os.path

def main(lookup_table_location):
    # Load the artist lookup table into memory:
    '''
    with open(lookup_table_location) as fp:
        lookup_table_json = json.load(fp=fp)
    pass
    '''

if __name__ == '__main__':
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    lookup_table_loc = storage_dir + "\\ArtistLookupTables\\Spotify\\SortedTrackLookupTable.json"
    main(lookup_table_location=lookup_table_loc)
