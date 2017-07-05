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
from urllib.error import HTTPError
from lxml import etree
from enum import Enum

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
        target_artists_string_dict = json.load(fp=fp, object_hook=enum_decoder)
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
    # Declare the intended storage directory for the artist:
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    # Excluding the first element extract the elements containing artist info:
    for aid, artist_info in enumerate(artist_anchor_tags[1:]):
        artist_name = artist_info.text
        # If the artist has no associated URL, then ignore the tag (it most likely is a separator anyway)
        try:
            artist_url = 'http://ohhla.com/' + artist_info.get("href")
            artist_storage_dir = storage_dir + "\\OHLA\\Artists\\" + artist_name
            artist_identifier = len(target_artists)
            print("Recorded AID: %d, Artist: %s" % (artist_identifier, artist_name))
            target_artists[artist_identifier] = {
                'aid': artist_identifier,
                'name': artist_info.text,
                'url': artist_url,
                'storage_dir': artist_storage_dir,
                'albums': None,
                'resume_target': (0, 0),
                'scraped': ScraperStatus.stage_zero
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
        json.dump(target_artists, fp, indent=4, cls=EnumEncoder)


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
        try:
            os.makedirs(artist_storage_dir)
            print("Local storage directory did not exist, instantiated!")
        except OSError:
            print("OSError Exception: Issued during creation of artist storage directory on HDD.")


def web_scrape_albums(target_artist):
    """
    web_scrape_albums -Records the following information about each album found under the provided target_artist_url:
        1. alid: The artist-unique identifier for the album (same ALID's exist across multiple artists).
        2. name: The name of the album as a human-readable string.
        3. url: The url marking the location of the album on the web as obtained by the webscraper.
        4. storage_dir: The target storage directory for files belonging to this album.
        5. songs: A list of song objects corresponding to this particular album.
        6. scraped: A boolean flag indicating whether every song on this album has been scraped. If True, all songs on
         this album have been recorded. If False, the associated artist contains a resume_target field indicating which
         songs have yet to be scraped on this album.
        7. resume_scrape_target: A tuple containing targeting information for resuming an unfinished web scrape:
         resume_alid: The unique (for this artist) album identifier indicating where scraping should resume from.
         resume_sid: The unique (for this album) song identifier indicating which track scraping should resume from.
    :param target_artist: The artist whose albums are to be scraped and returned.
    :return albums: The album metadata for the supplied target_artist
    """
    albums = {}
    if target_artist['resume_target'] is None:
        # Specific album targeted for resuming scrape.
        # TODO: Implement this logic.
        print("Critical: Functionality for resume web scrape album not built yet.")
    else:
        # ALID not recorded for scrape target, record all album info.
        # Open url to the target artist's web page with GET request:
        try:
            html_response = urlopen(target_artist['url'])
        except HTTPError as err:
            print("HTTPError: Critical error 404, file not found. Reason: %s" % err.reason)
            print("Blacklisting artist, removing from 'target_artists.json' and proceeding to next artist.")
            return None
        # Parse the HTML Response:
        html_parser = etree.HTMLParser()
        # Create an lxml tree for xpath extraction:
        tree = etree.parse(html_response, html_parser)
        # Point xpath target to the <tr> following the <tr> containing the text 'Parent Directory'
        # artist_album_list_start_xpath = "//body/table/tr/td/a[text()='Parent Directory']/.."
        # Record the number of <tr> elements:
        num_tr = int(tree.xpath("count(//body/table/tr)"))
        # Subtract the three preceding th elements:
        num_tr -= 3
        # Subtract the ending th element:
        num_tr -= 1
        # Construct an xpath selector for every td containing an album:
        tr_index = 4
        artist_album_list_xpaths = []
        for i in range(num_tr):
            containing_table_xpath = "//body/table/tr"
            album_xpath = containing_table_xpath + '[' + str(tr_index) + ']/td/a'
            artist_album_list_xpaths.append(tree.xpath(album_xpath)[0])
            tr_index += 1
        # Extract information for dictionary construction:
        for i, xpath_element in enumerate(artist_album_list_xpaths):
            # Specify a unique album ID for this artist:
            album_name = xpath_element.get('href')[0:-1]
            album_url = target_artist['url'] + album_name
            albums[i] = {
                'alid': i, 'name': album_name,
                'url': album_url,
                'storage_dir': target_artist['storage_dir'] + "\\" + album_name,
                'songs': None,
                'scraped': None
            }
    return albums


def initialize_album_storage_directory(album_info):
    """
    initialize_album_storage_directory: Checks to see if the album already has a directory created on the
     local machine. If no such directory is found then a directory under the provided name is
     created upnder Data/OHLA/Artists/<ALBUM_ARTIST>/<ALBUM_NAME>.
    :param album_info: All scraped information regarding the album.
    :return None: Upon completion, a new directory is created as Data/OHLA/Artists/<ALBUM_ARTIST>/<ALBUM_NAME>
     if no such directory had previously existed. If said directory had existed, it is left unmodified.
    """
    if dir_exists(album_info['storage_dir']):
        print("Local storage directory already exists, no need to instantiate.")
    else:
        try:
            os.makedirs(album_info['storage_dir'])
            print("Local storage directory did not exist, instantiated!")
        except OSError:
            print("OSError Exception: Issued during creation of artist storage directory on HDD.")


def main(target_artists):
    for i in range(len(target_artists)):
        print("Web-Scraper: Determining Artist to Resume Scraping At...")
        resume_target_aid = get_target_artist_to_scrape(target_artists)
        target_artist = target_artists[resume_target_aid]
        print("Done. Resuming data retrieval at AID: %d, Name: %s, URL: %s." % (
                target_artist['aid'], target_artist['name'], target_artist['url']))
        print("Determining if local storage directory for artist exists already...")
        initialize_artist_storage_directory(artist_name=target_artist['name'])
        # Update artists status in the IR-Pipeline:
        target_artist['scraped'] = ScraperStatus.stage_one
        target_artists[target_artist['aid']] = target_artist
        print("Performing second web scraper pass, retrieving album metadata")
        albums = web_scrape_albums(target_artist=target_artist)
        # if albums is None then artist was blacklisted due to some technical difficulty:
        if albums is not None:
            # Update the container data structure:
            target_artist['albums'] = albums
            target_artist['resume_target'] = (None, None)
            # Initialize a storage directory for every album the artist has:
            for alid, album_info in albums.items():
                initialize_album_storage_directory(album_info)
            # Update the artist's status in the IR-Pipeline:
            target_artist['scraped'] = ScraperStatus.stage_two
            target_artists[target_artist['aid']] = target_artist
            # Done scraping this artist's album-metadata-dump record information to json:
            write_target = target_artist['storage_dir'] + "\\album_metadata.json"
            try:
                with open(write_target, 'w') as fp:
                    json.dump(albums, fp=fp, indent=4)
            except OSError as err:
                print("OSError: Artist name is too weird. Blacklisting artist.")
                del target_artists[target_artist['aid']]
            print("Artist Album metadata stored and album directories created.")
            # Update global artist metadata json on local HDD in case of program termination:
            write_target_artists_to_json(target_artists=target_artists, write_dir=target_artists_loc)
        else:
            # Artist was blacklisted, their data couldn't be retrieved.
            # Scrub the artist from target_artists.json:
            del target_artists[target_artist['aid']]
            # TODO: Write more elegant code which retains a list of blacklisted artists for analysis and debugging.


class ScraperStatus(Enum):
    """
    ScraperStatus: An Enumerated type representing the status of the this artist in the information retrieval pipeline.
    Status assignments proceed as follows:
     stage_zero: Artist metadata has been retrieved via target_artists.json or just fetched via web-scraper. A new
        directory for the artist has not been created yet and the information persists only in memory.
     stage_one: Artist metadata has been retrieved via target_artists.json. A new directory for information retrieved
        about the artist has been created under Data\OHLA\Artists.
     stage_two: Album metadata (excluding songs) has been retrieved via web-scraper. A new directory for information
        retrieved about the album's songs has been created as Data\OHLA\Artists\<ARTIST_NAME>\<ALBUM_NAME>.
     stage_three: Song HTML information has been retrieved but not yet parsed. HTML data has been stored at the
        directory Data\OHLA\Artists\<ARTIST_NAME>\<ALBUM_NAME>\<SONG_NAME>.
     stage_four: Song lyrics have been parsed into plain-text. Automatically generated transcriptions have not yet
        been performed.
    """
    stage_zero = 0
    stage_one = 1
    stage_two = 2
    stage_three = 3
    stage_four = 4


class EnumEncoder(json.JSONEncoder):
    """
    EnumEncoder: This class enables the ScraperStatus Enum to be JSON encodable. This method is only called as a hook
     via json.dump().
    :source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
    """
    def default(self, obj):
        if type(obj) is ScraperStatus:
            # str(obj) is of type: 'ScraperStatus.stage_zero'
           return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)


def enum_decoder(dict):
    """
    enum_decoder: This method enables the ScraperStatus Enum to be JSON decodable (read with json.load()).
    :param dict: The dictonary returned by json.load, this method is called only as a hook.
    :return attribute: The ScraperStatus.member that the provided string actually belongs to.
    :source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
    """
    if "__enum__" in dict:
        name, member = dict["__enum__"].split(".")
        return getattr(ScraperStatus, member)
    else:
        return OrderedDict(dict)

if __name__ == '__main__':
    """
    Performs as follows:
    1. Determines existence of a target_artists.json file which contains a list of artists to scrape and their
        associated urls.
        * If this file does not exist, it is created.
        * If this file does exist, target information for the web-scraper is loaded into memory and web-scraping is
            resumed by original order of retrieval for artists.
    2.
    """
    # Instantiate the storage directory relative to this file in the project hierarchy:
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    # Construct the target directory for the file containing artist metadata:
    artist_metadata_loc = storage_dir + "\\OHLA\\WebScraper\\MetaData\\"
    target_artists_loc = storage_dir + "\\OHLA\\WebScraper\\MetaData\\target_artists.json"
    if file_exists(fpath=target_artists_loc):
        # The file containing target metadata was found, load into memory:
        print("Init: 'target_artists.json' file found. Loading web-scraping target URL's into memory.")
        target_artists = load_web_scraper_target_urls(target_artists_loc)
        print("Init: Target URL's loaded into memory. Proceeding to main Web-Scraper loop.")
    else:
        # The file containing target metadata was not found. Initialize web scraper to obtain target information.
        print("Init: 'target_artists.json' not found. Initializing URL targets via Web-Scrape...")
        target_artists = web_scrape_artist_meta_data()
        # Write the metadata to the hard-drive for retrieval:
        write_target_artists_to_json(target_artists, target_artists_loc)
        print("Init: 'target_artists.json' written to hard drive. Proceeding to main Web-Scraper loop.")
    main(target_artists=target_artists)

