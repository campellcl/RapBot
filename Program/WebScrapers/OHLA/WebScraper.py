"""
WebScraper.py
Performs retrieval of plaintext song lyrics from The Online Hip Hop Lyrics Archive (OHLA).
Utilizes the SortedTrackLookupTable.json file to determine the artists to target.
"""
import json
from urllib.request import urlopen
from lxml import etree
from io import StringIO
import os.path
from pathlib import Path
from collections import OrderedDict

def main():
    pass

def web_scrape_artists(target_artist_storage_dir):
    """
    web_scrape_artists - Scrapes all artists and records their parsed information, then dumps to a JSON file at the
        specified storage directory.
    :param target_artist_storage_dir: The location for which to dump the JSON file generated during scraping.
    :return target_artists: The dictionary containing information about scraped artists.
    """
    '''Initialize Storage Structure'''
    target_artists = OrderedDict()
    '''Initialize Scraping URL's'''
    artist_list_url_a_thru_e = "http://ohhla.com/all.html"
    artist_list_url_f_thru_j = "http://ohhla.com/all_two.html"
    artist_list_url_k_thru_o = "http://ohhla.com/all_three.html"
    artist_list_url_p_thru_t = "http://ohhla.com/all_four.html"
    artist_list_url_u_thru_z = "http://ohhla.com/all_five.html"
    '''Scrape All Artist Names'''
    target_artists = parse_artist_info(target_artists=target_artists, artist_list_url=artist_list_url_a_thru_e)
    target_artists = parse_artist_info(target_artists=target_artists, artist_list_url=artist_list_url_f_thru_j)
    target_artists = parse_artist_info(target_artists=target_artists, artist_list_url=artist_list_url_k_thru_o)
    target_artists = parse_artist_info(target_artists=target_artists, artist_list_url=artist_list_url_p_thru_t)
    target_artists = parse_artist_info(target_artists=target_artists, artist_list_url=artist_list_url_u_thru_z)
    '''Perform JSON Dump of Scraped Artist Data'''
    write_target_artists_to_json(target_artists, target_artists_loc)
    return target_artists

def parse_artist_info(target_artists, artist_list_url):
    """
    Takes a dictionary that is partially completed or completely blank. Will populate dictionary based on the target
        url passed in via artist_list_url.
    :param target_artists: Either an empty or partially populated dictionary of artists.
    :param artist_list_url: The url to scrape artists from, and append to the target_artists dictionary.
    :return: target_artists: The provided dictionary of artists now updated with the content found on the page
        specified by artist_list_url.
    """
    # Open url to the webpage with GET request:
    html_response = urlopen(artist_list_url)
    # Parse the HTML Response:
    html_parser = etree.HTMLParser()
    # Create an lxml tree for xpath extraction:
    tree = etree.parse(html_response, html_parser)
    # result = etree.tostring(tree, pretty_print=True, method='html')
    artist_anchor_tags_xpath = "//body//div[@id='leftmain']//pre"
    artist_anchor_tags = tree.xpath(artist_anchor_tags_xpath)[0].getchildren()
    # Excluding the first element extract the elements containing artist info:
    for aid, artist_info in enumerate(artist_anchor_tags[1:]):
        artist_name = artist_info.text
        # If the artist has no associated URL, then ignore the tag (it most likely is a separator anyway)
        try:
            artist_url = 'http://ohhla.com/' + artist_info.get("href")
            artist_identifier = len(target_artists)
            print("Recorded AID: %d, Artist: %s" %(artist_identifier, artist_name))
            target_artists[artist_identifier] = {
                'AID': artist_identifier,
                'name': artist_info.text,
                'url': artist_url,
                'scraped': False
            }
        except Exception:
            # The artist either has no associated URL or this is just a placeholder HTML tag.
            pass
    return target_artists

def write_target_artists_to_json(target_artists, write_dir):
    """
    write_target_artists_to_json -Writes the provided dictionary of artists to the specified write directory in json format.
    :param target_artists: The dictionary composed of artists and their associated urls.
    :param write_dir: The specified directory where the json file should be written.
    :return:
    """
    with open(write_dir, 'w') as fp:
        json.dump(target_artists, fp, indent=4)

if __name__ == '__main__':
    """
    Main pre-initialization method. Performs initial scraping of artists if no target file exists, otherwise loads
    required information into memory. Initializes storage directory pointers.
    """
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    target_artists_loc = storage_dir + "\\OHLA\\WebScraper\\Artists\\target_artists.json"
    scraping_log_loc = storage_dir + "\\OHLA\\HTLML"
    lookup_table_loc = storage_dir + "\\ArtistLookupTables\\Spotify\\SortedTrackLookupTable.json"
    # Determine if target_artists.json exists:
    target_artists_json = Path(target_artists_loc)
    if target_artists_json.is_file():
        # The target_artists.json file exists, load into memory
        print("Init: 'target_artists.json' file found. Loading scraping target URL's into memory...")
        with open(target_artists_loc, 'r+') as fp:
            # Load the target_artists.json file as an OrderedDictionary:
            target_artists_string_dict = json.load(fp=fp, object_pairs_hook=OrderedDict)
            print("Init: Success! Target URL's loaded into memory. Converting back to integer representation...")
            target_artists = {int(k): v for k, v in target_artists_string_dict.items()}
            pass
    else:
        # File does not exist, scrape artists and dump to json.
        print("Init: 'target_artists.json' not found. Re-initializing url targets via new WebScrape...")
        target_artists = web_scrape_artists(target_artist_storage_dir=target_artists_loc)
