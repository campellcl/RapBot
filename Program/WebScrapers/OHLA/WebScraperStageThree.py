"""
WebScraperStageThree.py
Obtains the song data for the albums specified in the target_artists.json file. Writes each song to a newly created
directory housed under Data/OHLA/Artists/<YOUR_ARTIST>/<YOUR_ALBUM>/<NEW_SONG>.
"""

import os.path
from pathlib import Path
import json
from enum import Enum
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import HTTPError
from lxml import etree
import io

__author__ = "Chris Campell"
__version__ = "7/5/2017"


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

    def __eq__(self, obj):
        # Attempt to type cast the comparison object to this class:
        try:
            scraper_status_obj = ScraperStatus(obj)
        except Exception as exc:
            print("ScraperStatus: Failure to typecast foreign object during comparison. Exception states: %s"
                  % exc.__cause__)
        if type(obj) is type(self):
            return self.value == scraper_status_obj.value


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
    :param dict: The dictionary returned by json.load, this method is called only as a hook.
    :return attribute: The ScraperStatus.member that the provided string actually belongs to.
    :source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
    """
    if "__enum__" in dict:
        name, member = dict["__enum__"].split(".")
        return getattr(ScraperStatus, member)
    else:
        return OrderedDict(dict)


def file_exists(fpath):
    """
    file_exists: Returns True if the provided file path results in a accessible file on the local machine; returns
        False otherwise.
    :param fpath: A string representation of a file path pointing at a file on the local machine.
    :return Boolean: True if the file path points to an existing file on the local machine, False otherwise.
    """
    file_path = Path(fpath)
    return file_path.is_file()


def dir_exists(dir_path):
    """
    dir_exists: Determines whether the specified directory exists on the local machine.
    :param dir_path: The directory for which to test for existence.
    :return Boolean: True if the directory exists on the local machine, False otherwise.
    """
    return os.path.isdir(dir_path)


def load_web_scraper_target_urls(target_artists_loc):
    """
    load_web_scraper_target_urls: Helper method, loads the list of artists, albums, and their associated URLs
        into memory. The web-scraper will use this target list of URLs to scrape the song information for each album.
    :param target_artists_loc: The pre-validated (file_exists(fpath)) storage directory of the json file containing
     the list of artists, unique identifiers, and target urls for scraping.
    :return target_artists: A dictionary of artists sorted by unique identifier AID (assigned by order of encounter),
     and their associated URL's for the web-scraper to target.
    """
    with open(target_artists_loc, 'r') as fp:
        # Load the target_artists.json file as an OrderedDictionary, hook into custom enum decoder for ScraperStatus:
        target_artists_string_dict = json.load(fp=fp, object_hook=enum_decoder)
        # print("Init: Success! Target URL's loaded into memory. Converting back to integer representation.")
        target_artists = {int(k): v for k, v in target_artists_string_dict.items()}
    return target_artists


def write_target_artists_to_json(target_artists, write_dir):
    """
    write_target_artists_to_json: Writes the provided metadata dictionary to the specified write directory in the
     JSON format.
    :param target_artists: The dictionary composed of artist metadata.
    :param write_dir: The specified directory where the json file should be written to.
    :return None: Upon completion the provided target_artists dictionary will be written to the specified write_dir.
    """
    with open(write_dir, 'w') as fp:
        json.dump(target_artists, fp, indent=4, cls=EnumEncoder)


def web_scrape_target_songs(target_album):
    """
    web_scrape_target_songs: Scrapes the list of songs for URL metadata found at the album's url
        (specified in 'target_album').
    :param target_album: The album for which all song metadata (and urls) are to be retrieved for.
    :return target_songs: A dictionary of songs and associated metadata (excluding ascii text) for the provided album.
    """
    target_songs = OrderedDict()
    try:
        # Open url to the target albums web page with GET request:
        html_response = urlopen(target_album['url'])
    except HTTPError as err:
        print("HTTPError: Critical error 404, file not found. Reason: %s" % err.reason)
        print("HTTPError: Failure to retrieve target songs for album ALID: %d (%s) at URL: %s"
              % (target_album['alid'], target_album['name'], target_album['url']))
        # TODO: Log the album that the program failed to retrieve for further analysis.
        return None
    # Parse the HTML Response:
    html_parser = etree.HTMLParser()
    # Create an lxml tree for xpath extraction:
    tree = etree.parse(html_response, html_parser)
    # Record the number of <tr> elements that are actual songs for indexing:
    num_tr = int(tree.xpath("count(//body/table/tr)"))
    # Subtract the ending <tr> and leading three <tr>'s which contain no song info:
    num_tr -= 4
    # Start for-loop iteration at the specified index:
    tr_index = 4
    target_song_xpaths = []
    # Iterate over every song in the <tbody>:
    for i in range(num_tr):
        containing_table_xpath = "//body/table/tr"
        target_song_xpath = containing_table_xpath + '[' + str(tr_index) + ']/td/a'
        target_song_xpaths.append(tree.xpath(target_song_xpath)[0])
        tr_index += 1
    # Parse information for dictionary construction:
    for i, xpath_element in enumerate(target_song_xpaths):
        song_name = xpath_element.get('href')[0:]
        song_url = target_album['url'] + "/" + song_name
        song_storage_dir = target_album['storage_dir'] + "\\" + song_name[:-4]
        target_songs[i] = {
            'sid': i,
            'name': song_name,
            'url': song_url,
            'storage_dir': song_storage_dir,
            'ascii': None
        }
    return target_songs


def web_scrape_song_plaintext(target_song):
    """
    web_scrape_song_plaintext: Given a song's metadata (sid, url, storage_dir, etc...) scrapes the ascii plaintext
     found at the URL associated with the provided target_song.
    :param target_song: The metadata of the song to be scraped.
    :return:
    """
    plain_text = None
    try:
        # Open url to the target albums web page with GET request:
        html_response = urlopen(target_song['url'])
    except HTTPError as err:
        print("HTTPError: Critical error 404, file not found. Reason: %s" % err.reason)
        # TODO: Log the song that the program failed to retrieve for further analysis.
        return None
    # Parse the HTML Response:
    html_parser = etree.HTMLParser()
    # Create an lxml tree for xpath extraction:
    tree = etree.parse(html_response, html_parser)
    # It is usually the third <div> element that contains the lyrics:
    target_ascii_xpath = "//body/div[3]/pre"
    try:
        ascii_xpath = tree.xpath(target_ascii_xpath)[0]
    except Exception as exception:
        print("Exception (cause: %s) encountered while parsing plaintext lyrics at %s. Trying to "
              "scrape plaintext from single leading <pre> tag." % (exception.__cause__, target_song['url']))
        try:
            target_ascii_xpath = "//body/p"
            ascii_xpath = tree.xpath(target_ascii_xpath)[0]
            print("Success, data obtained using fallback xpath. Verify contents of the directory (%s) are correct."
                  % target_song['storage_dir'])
        except Exception as exception:
            print("Exception (cause: %s) still encountered while attempting backup plaintext parse at %s. Programmer "
                  "intervention required!" %(exception.__cause__, target_song['url']))
    plain_text = ascii_xpath.text
    return plain_text


def init_song_storage_dir(target_song):
    """
    initialize_artist_storage_directory: Checks to see if the song already has a directory created on the
     local machine. If no such directory is found then a directory under the provided target_song['name'] is
     created under Data/OHLA/Artists/<ARTIST_NAME>/<ALBUM_NAME>/.
    :param target_song: The song for which the storage directory is to be created.
    :return None: Upon completion, a new directory is created as Data/OHLA/Artists/<ARTIST_NAME>/<ALBUM_NAME> if
     no such directory had previously existed. If said directory had existed, it is left unmodified.
    """
    target_storage_dir = target_song['storage_dir']
    if dir_exists(target_storage_dir):
        # print("Target Directory already exists at: %s" % target_song['storage_dir'])
        pass
    else:
        try:
            os.makedirs(target_storage_dir)
            # print("Local storage directory did not exist, instantiated!")
        except OSError as err:
            print("OSError Exception: Issued during creation of artist storage directory on HDD. Error reads: %s"
                  % err.reason)


def main(target_artists):
    # Scrape every artist's song data:
    for aid, artist_info in target_artists.items():
        # If the artist has already reached stage_three in the IR pipeline, then ignore.
        if artist_info['scraped'].value != ScraperStatus.stage_three.value:
            # print("Scraping Artist AID: %d (%s) songs." %())
            for alid, album_info in artist_info['albums'].items():
                # If the album has already been scraped entirely than ignore.
                if not album_info['scraped']:
                    # Parse song meta-information:
                    target_songs = web_scrape_target_songs(target_album=album_info)
                    if target_songs is None:
                        # Target urls could not be retrieved, skip this album.
                        break
                    # Parse song ASCII (plain-text) for every song:
                    for sid, song_info in target_songs.items():
                        plain_text = web_scrape_song_plaintext(song_info)
                        if plain_text is not None:
                            # Update containing data structure:
                            target_songs[sid]['ascii'] = plain_text
                            # target_songs[sid]['ascii'] = plain_text.encode("utf-8")
                            target_artists[aid]['resume_target'] = (alid, sid)
                            # Create song storage directory on local HDD:
                            init_song_storage_dir(target_song=target_songs[sid])
                            # Write plaintext to storage directory as file:
                            with open(target_songs[sid]['storage_dir'] + "/ascii.txt", 'w', encoding='utf-8') as fp:
                                fp.write(plain_text)
                        else:
                            # TODO: If both web-scraping attempts fail
                            print("\t\tWS[StageThree]: Warning, both Web-Scraper attempts failed. Programmer "
                                  "action required!")
                    # Update containing data structure:
                    target_artists[aid]['albums'][alid]['songs'] = target_songs
                    target_artists[aid]['albums'][alid]['scraped'] = True
                    # Update metadata container on HDD:
                    write_location = artist_metadata_loc + "target_artists_stage_three.json"
                    write_target_artists_to_json(target_artists, write_location)
                    # Print status update:
                    print("\tWS[StageThree]: Backed up to hard drive. Finished scraping album ALID: "
                          "%s (%s) for artist AID: %s (%s)" %(alid, album_info['name'], aid, artist_info['name']))
                else:
                    # The album has already been scraped in its entirety:
                    print("\tWS[StageThree]: The album ALID: %s (%s) for artist AID: %s (%s) has already been scraped "
                          "and stored. Skipping to next unscraped album." %
                          (alid, album_info['name'], aid, artist_info['name']))
            # Update metadata information for artist:
            target_artists[aid]['resume_target'] = (None, None)
            target_artists[aid]['scraped'] = ScraperStatus.stage_three
            print("WS[StageThree]: Backed up to hard drive. Finished scraping song info for artist AID: %d (%s)"
                  % (aid, artist_info['name']))
        else:
            print("WS[StageThree]: Artist AID: %d (%s) was already scraped and recorded, proceeding."
                  % (aid, artist_info['name']))


if __name__ == '__main__':
    ''' Initialize storage directory paths and pre-requisite file pointers. Load necessary data. '''
    # Instantiate the storage directory relative to this file in the project hierarchy:
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/'
    ))
    # Construct the target directory for the file containing artist metadata:
    artist_metadata_loc = storage_dir + "\\OHLA\\WebScraper\\MetaData\\"
    target_artists_loc = storage_dir + "\\OHLA\\WebScraper\\MetaData\\target_artists_stage_three.json"
    # Ensure target_artists.json exists:
    if not file_exists(fpath=target_artists_loc):
        print("Init: Critical Error! Could not find the specified source file: 'target_artists.json'.")
        print("Init: To re-generate 'target_artists.json' run WebScraperTwo.py "
              "(the first and second web scraper stages). Aborting execution.")
        exit(-1)
    target_artists = load_web_scraper_target_urls(target_artists_loc=target_artists_loc)
    # TODO: Convert the target_artists Enum to IntEnum as the equality operator for Enum does 'name' and
    #   not 'member' comparisons.
    main(target_artists=target_artists)

