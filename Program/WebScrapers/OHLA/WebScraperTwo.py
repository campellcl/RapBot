"""
WebScraperTwo.py
Performs retrieval of plaintext song lyrics from The Online Hip Hop Lyrics Archive (OHLA). Refactored version of the
original WebScraper.py which utilizes OOP to enhance code readability.
"""
import os.path
from pathlib import Path
import json
from collections import OrderedDict
from urllib.request import urlopen
from lxml import etree

__author__ = "Chris Campell"
__version__ = "7/3/2017"


def file_exists(fpath):
    """
    file_exists: Returns True if the provided file path results in a accessible file on the local machine; returns
        False otherwise.
    :param fpath: A string representation of a file path pointing at a file on the local machine.
    :return Boolean: True if the file path points to an existing file on the local machine, False otherwise.
    """
    file_path = Path(fpath)
    return file_path.is_file()


def load_web_scraper_target_urls(target_artists_loc):
    """
    load_web_scraper_target_urls: Helper method, loads the list of artists and their associated URLs into memory. The
        web-scraper will use this target list of URLs to scrape the album meta-information for each target url.
    :param target_artists_loc: The pre-validated (file_exists(fpath)) storage directory of the json file containing
     the list of artists, unique identifiers, and target urls for scraping.
    :return target_artists: A dictionary of artists sorted by unique identifier AID (assigned by order of encounter),
     and their associated URL's for the web-scraper to target.
    """
    with open(target_artists_loc, 'r') as fp:
        # Load the target_artists.json file as an OrderedDictionary:
        target_artists_string_dict = json.load(fp=fp, object_pairs_hook=OrderedDict)
        # print("Init: Success! Target URL's loaded into memory. Converting back to integer representation.")
        target_artists = {int(k): v for k, v in target_artists_string_dict.items()}
    return target_artists


def get_target_artist_to_scrape(target_artists):
    """
    get_target_artist_to_scrape: Returns the unique artist identifier (AID) of the artist for which scraping
     operations are to resume at.
    :param target_artists: The json file containing the list of artists and their desired URL's for web scraping.
    :return aid: The unique identifier indicating the artist to resume scraping at.
    """
    for aid, artist_info in target_artists.items():
        resume_target = artist_info['resume_target']
        # If the tuple contains an album identifier (ALID) to resume scraping at:
        if resume_target[0] is not None:
            return aid

def parse_artist_info(target_artists, artist_list_url):
    """
    parse_artist_info: Helper method for web_scrape_artist_metadata. Takes either an empty or partially filled
     dictionary. The provided dictionary will be populated with meta-information scraped from the list of artists found
     at the provided artist_list_url. The following information is retained for each artist:
     1. AID: A unique identifier for the artist.
     2. name: The string representation of the artist's name.
     3. url: The url associated with the artist.
     4. resume_target: A tuple containing target indices for the web scraper indicating where in the artist's works
        web-scraping should resume from. This method sets resume_target to (None, None) but generally resume_Target will
        take the form (ALID, SID) where:
        A) ALID (ALbum IDentifier) indicates the album where scraping should resume from.
        B) SID (Song IDentifier) indicates the album's track where scraping should resume from.
    :param target_artists: Either an empty or partially populated dictionary of artists containing the information that
     is detailed above.
    :param artist_list_url: A url on the web-site containing a list of artists to be scraped.
    :return target_artists: The provided dictionary of artists now updated with the content found on the page
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
            print("Recorded AID: %d, Artist: %s" % (artist_identifier, artist_name))
            target_artists[artist_identifier] = {
                'AID': artist_identifier,
                'name': artist_info.text,
                'url': artist_url,
                'resume_target': (0, 0)
            }
        except Exception:
            # The artist either has no associated URL or this is just a placeholder HTML tag.
            pass
    return target_artists


def web_scrape_artist_meta_data():
    """
    web_scrape_artist_meta_data: Initializes a Web-Scraper to obtain key information for the next Web-Scraper pass. This
     pass of the Web-Scraper creates a dictionary containing meta-information such as the artist's unique identifier
     and the storage location for the Artist's albums on the HDD.
    :return target_artists: The dictionary containing meta-information for artists.
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
    return target_artists


def write_target_artists_to_json(target_artists, write_dir):
    """
    write_target_artists_to_json: Writes the provided dictionary of artists to the specified write directory in the
     JSON format.
    :param target_artists: The dictionary composed of artists and their associated urls.
    :param write_dir: The specified directory where the json file should be written to.
    :return None: Upon completion the provided target_artists dictionary will be written to the specified write_dir.
    """
    with open(write_dir, 'w') as fp:
        json.dump(target_artists, fp, indent=4)


def dir_exists(dir_path):
    """
    dir_exists: Determines whether the specified directory exists on the local machine.
    :param dir_path: The directory for which to test for existence.
    :return Boolean: True if the directory exists on the local machine, False otherwise.
    """
    return os.path.isdir(dir_path)

def initialize_artist_storage_directory(artist_name):
    """
    initialize_artist_storage_directory: Checks to see if the artist already has a directory created on the
     local machine. If no such directory is found then a directory under the provided name is
     created upnder Data/OHLA/Artists/<YOUR_NAME_HERE>.
    :param artist_name: The name of the artist by which to create the directory.
    :return None: Upon completion, a new directory is created as Data/OHLA/Artists/<YOUR_NAME_HERE> if no such
     directory had previously existed. If said directory had existed, it is left unmodified.
    """
    global_storage_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../..', 'Data/'
    ))
    artist_storage_dir = global_storage_dir + "\\OHLA\\Artists\\" + artist_name
    if dir_exists(artist_storage_dir):
        print("Local storage directory already exists, no need to instantiate.")
    else:
        print("Local storage directory does not exist, instantiating...")
        try:
            os.makedirs(artist_storage_dir)
        except OSError:
            print("OSError Exception: Issued during creation of artist storage directory on HDD.")

def main(target_artists):
    for i in range(len(target_artists)):
        print("Web-Scraper: Determining Artist to Resume Scraping At...")
        resume_target_aid = get_target_artist_to_scrape(target_artists)
        target_artist = target_artists[resume_target_aid]
        print("Done. Resuming data retrieval at AID: %d, Name: %s, URL: %s." % (
                target_artist['AID'], target_artist['name'], target_artist['url']))
        print("Determining if local storage directory for artist exists already...")
        initialize_artist_storage_directory(artist_name=target_artist['name'])



if __name__ == '__main__':
    """
    Performs as follows:
    1. Determines existence of a target_artists.json file which contains a list of artists to scrape and their
        associated urls.
        * If this file does not exist, it is created.
        * If this file does exist, target information for the web-scraper is loaded into memory and web-scraping is
            resumed as specified.
    """
    # Instantiate the storage directory relative to this file in the project hierarchy:
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    # Construct the target directory for the file containing artist metadata:
    target_artists_loc = storage_dir + "\\OHLA\\WebScraper\\MetaData\\target_artists.json"
    if file_exists(fpath=target_artists_loc):
        # The file containing target metadata was found, load into memory:
        print("Init: 'target_artists.json' file found. Loading web-scraping target URL's into memory.")
        target_artists = load_web_scraper_target_urls(target_artists_loc)
        print("Init: Target URL's loaded into memory. Proceeding to main Web-Scraper loop.")
    else:
        # The file containing target metadata was not found. Initialize web scraper to obtain target information.
        print("Init: 'target_artists.json' not found. Re-initializing URL targets via Web-Scrape...")
        target_artists = web_scrape_artist_meta_data()
        # Write the metadata to the hard-drive for retrieval:
        write_target_artists_to_json(target_artists, target_artists_loc)
        print("Init: 'target_artists.json' written to hard drive. Proceeding to main Web-Scraper loop.")
    main(target_artists=target_artists)

