"""
WebScraperThree.py
Modified version of the WebScraper created to resolve issues with the first two generations. Particularly this version
of the WebScraper abandons the single-file metadata approach (target_artists.json). Instead this version of the
web scraper relies on an individual json file for each artist, and an individual json file for each song. The json
file for each song contains scraped ASCII, cleaned ASCII, g2p transcription, and failed transcription information.
"""

import os.path
from pathlib2 import Path
from enum import Enum
from collections import OrderedDict
from urllib.request import urlopen
from lxml import etree
import json

__author__ = "Chris Campell"
__created__ = "7/13/2017"
__version__ = "7/18/2017"


class ScraperStatus(Enum):
    """
    ScraperStatus: An Enumerated type representing the status of the this artist in the information retrieval pipeline.
    Status assignments proceed as follows:
     stage_zero: Artist metadata (aid, name, url, resume_target, storage_dir, scrape_status) has been recorded in the
        scaper_metadata.json file. The artist's storage directory has been initialized.
        * AID: Unique Identifier (integer).
        * name: Artist's name (string).
        * url: The URL for the artists page.
        * resume_target: A tuple (alid, sid) which contains target information for where the WebScraper last left off
            scraping for this particular artist. ALID indicates the unique album identifier, SID indicates the unique
            song identifier associated with the album in question. Scraping is to resume at the specified indices. If
            the resume_target: (-1, -1) then scraping has not started yet for this artist. In the event that the
            resume_target: (None, None) then scraping has been finished for this artist.
        * storage_dir: A string representing the storage directory for the artist relative to the project root.
        * scrape_status: A member of this class indicating status in the IR pipeline.
     stage_one: Artist's storage directory has been initialized on the local machine.
     stage_two: Artist's album metadata has been recorded under the artist's directory as album_name_metadata.json.
        metadata retained for the albums include (assoc_aid, alid, name, url, storage_dir, scraped):
        * assoc_aid: The artist's unique identifier (int).
        * alid: The album's unique identifier (int).
        * name: The album's name (string).
        * url: The album's url (string).
        * storage_dir: The album's storage directory on the local machine (string).
        * scraped: A boolean flag indicating whether or not the album has been scraped in its entirety.
     stage_three: All album's storage directories have been initialized on the local machine.
     stage_four: All of the artist's album's song metadata have been retrieved. All song's metadata has been stored in
        one file: album_song_metadata.json, constituting (assoc_alid, sid, name, url, storage_dir, song_scraped_status):
        * assoc_alid: The containing album's unique identifier (int).
        * sid: The song's unique identifier (int).
        * name: The song's name (string).
        * url: The song's url (string).
        * storage_dir: The song's storage directory on the local machine (string).
        * song_scraped_status: A different Enum (TranscriptionStatus) that represents the status of the song in
            the IR pipeline.
        At this stage in the IR pipeline all processing has been performed for the artist. IR pipeline then proceeds
        for each individual song per the stages defined in the Enum: TranscriptionStatus.
    """
    stage_zero = 0
    stage_one = 1
    stage_two = 2
    stage_three = 3
    stage_four = 4

    def __eq__(self, obj):
        """
        __eq__: Overridden method which defines equality between two ScraperStatus objects.
        :param obj: The desired method to check equality with.
        :return bool: If the two objects are both of type ScraperStatus and share the same value, True is returned.
         If both objects are of type ScraperStatus and do not share the same value, False is returned. Otherwise an
         exception is generated and printed to the console before terminating the program.
        """
        # Attempt to type cast the comparison object to this class:
        try:
            scraper_status_obj = ScraperStatus(obj)
            if type(obj) is type(self):
                return self.value == scraper_status_obj.value
        except Exception as exc:
            print("ScraperStatus[__eq__]: Failure to typecast foreign object during comparison. Exception states: %s"
                  % str(exc))
            exit(-1)


class ScraperStatusEncoder(json.JSONEncoder):
    """
    ScraperStatusEncoder: This class enables the ScraperStatus Enum to be JSON encodable. This method is only called
     as a hook via json.dump().
    :source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
    """

    def default(self, obj):
        """
        default: Overridden method which encodes the provided ScraperStatus object as a string representation of its
         associated value.
        :param obj: The desired object (of type ScraperStatus) to be encoded in JSON Serializable form.
        :return dict: The string representation of the provided ScraperStatus enumerated constant.
        """
        if type(obj) is ScraperStatus:
            # str(obj) is of type: 'ScraperStatus.stage_zero'
           return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)


class TranscriptionStatus(Enum):
    """
    TranscriptionStatus: An Enumerated type representing the status of an individual song in the IR Pipeline.
    Status assignments proceed as follows:
     stage_zero: Song metadata has been recorded in the album_song_metadata.json underneath the containing album's
        storage directory.
     stage_one: Storage directories for each song have been created on the local machine.
     stage_two: Plaintext (ASCII) has been recorded for the song under it's associated directory created in stage two.
        The album's metadata has been updated with scraped = true if this is the last song in the album.
     stage_three: Automated Grapheme to Phoneme transcription has been performed for this song and written to the
        song's local storage directory. G2P transcription statistics have been recorded to the local directory as well.
    """
    stage_zero = 0
    stage_one = 1
    stage_two = 2
    stage_three = 3

    def __eq__(self, obj):
        # Attempt to type cast the comparison object to this class:
        try:
            transcription_status_obj = ScraperStatus(obj)
            if type(obj) is type(self):
                return self.value == transcription_status_obj.value
        except Exception as exc:
            print("TranscriptionStatus[__eq__]: Failure to typecast foreign object during comparison. "
                  "Exception states: %s" % str(exc))
            exit(-1)


class ProgramOperation(Enum):
    """
    ScraperOperation: An Enumerated Type representing the operation to perform during execution.
     scrape_artists: Perform the operations detailed in ScraperStatus for artists' stage_zero and stage_one.
     scrape_albums: Perform the operations detailed in ScraperStatus for artists' stage_two and stage_three.
     scrape_songs: Perform the operations detailed in ScraperStatus for artists' stage_four.
     transcribe_songs: Perform the operations detailed in TranscriptionStatus for songs' stage_zero through stage_three.
    """
    scrape_artists = 0
    scrape_albums = 1
    scrape_songs = 2
    transcribe_songs = 3

    def __eq__(self, obj):
        # Attempt to type cast the comparison object to this class:
        try:
            program_op_obj = ProgramOperation(obj)
            if type(obj) is type(self):
                return self.value == program_op_obj.value
        except Exception as exc:
            print("ProgramOperation[__eq__]: Failure to typecast foreign object during comparison. Exception states: %s"
                  % str(exc))
            exit(-1)


def file_exists(fpath):
    """
    file_exists: Returns True if the provided file path results in a accessible file on the local machine; returns
        False otherwise.
    :param fpath: A string representation of a file path pointing at a file on the local machine.
    :return Boolean: True if the file path points to an existing file on the local machine, False otherwise.
    """
    file_path = Path(fpath)
    return file_path.is_file()


def web_scrape_artists():
    """
    web_scrape_artists: Scrapes the following information for each artist and returns an ordered dictionary of the
     collected information.
    * AID: Unique Identifier (integer).
    * name: Artist's name (string).
    * resume_target: A tuple (alid, sid) which contains target information for where the WebScraper last left off
        scraping for this particular artist. ALID indicates the unique album identifier, SID indicates the unique
        song identifier associated with the album in question. Scraping is to resume at the specified indices. If
        the resume_target: (-1, -1) then scraping has not started yet for this artist. In the event that the
        resume_target: (None, None) then scraping has been finished for this artist.
    * storage_dir: A string representing the storage directory for the artist relative to the project root.
    * scrape_status: A member of this class indicating status in the IR pipeline.
    :return artists: An ordered dictionary of artists (sorted by AID) and their associated information as detailed
        above.
    """
    artists = OrderedDict()
    '''Initialize Scraping URL's'''
    artist_list_url_a_thru_e = "http://ohhla.com/all.html"
    artist_list_url_f_thru_j = "http://ohhla.com/all_two.html"
    artist_list_url_k_thru_o = "http://ohhla.com/all_three.html"
    artist_list_url_p_thru_t = "http://ohhla.com/all_four.html"
    artist_list_url_u_thru_z = "http://ohhla.com/all_five.html"
    ''' Scrape All Artist Metadata '''
    artists = parse_artist_info(artists=artists, artist_list_url=artist_list_url_a_thru_e)
    artists = parse_artist_info(artists=artists, artist_list_url=artist_list_url_f_thru_j)
    artists = parse_artist_info(artists=artists, artist_list_url=artist_list_url_k_thru_o)
    artists = parse_artist_info(artists=artists, artist_list_url=artist_list_url_p_thru_t)
    artists = parse_artist_info(artists=artists, artist_list_url=artist_list_url_u_thru_z)
    return artists


def parse_artist_info(artists, artist_list_url):
    """
    Takes a dictionary that is partially completed or completely blank. Will populate the dictionary based on
        the target url passed in via artist_list_url.
    :param artists: Either an empty or partially populated dictionary of artists.
    :param artist_list_url: The url to scrape artists from, and append to the target_artists dictionary.
    :return: artists: The provided dictionary of artists now updated with the content found on the page
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
            artist_identifier = len(artists)
            artist_name = artist_info.text
            artist_storage_dir = storage_dir + "\\Artists\\" + artist_name
            artists[artist_identifier] = {
                'AID': artist_identifier,
                'name': artist_name,
                'url': artist_url,
                'resume_target': (-1, -1),
                'storage_dir': artist_storage_dir,
                'scraper_status': ScraperStatus.stage_zero
            }
            # Note: A resume_target of (-1, -1) indicates that scraping has not yet resumed for this artist.
            print("WS3[parse_artist_info] Recorded AID: %d, Artist: %s" % (artist_identifier, artist_name))
        except Exception:
            # The artist either has no associated URL or this is just a placeholder HTML tag.
            pass
    return artists


def main(operation):
    if operation == ProgramOperation.scrape_artists:
        ''' Proceed with artist scraping IR Pipeline. '''
        print("WS3[main]: Program started with directive: SCRAPE_ARTISTS")
        # Check to see if the file containing metadata exists:
        if file_exists(scraper_metadata_json):
            print("WS3[main]: The file 'scraper_metadata.json' already exists. Artist info has already been retrieved."
                  " To reinitialize the metadata file delete 'scraper_metadata.json' and run the program again.")
        else:
            print("WS3[main]: The metadata file: 'scraper_metadata.json' was not found. Reinitializing metadata via"
                  " artist web scraper.")
            artists = web_scrape_artists()
            print("WS3[main]: Artist information retrieved. "
                  "There were %d artists retrieved successfully. Writing to HDD..." % len(artists))
            with open(scraper_metadata_json, 'w') as fp:
                json.dump(artists, fp, indent=4, cls=ScraperStatusEncoder)
            print("WS3[main]: Artist metadata stored on the HDD. Program terminating with successful exit.")
            exit(0)
    elif operation == ProgramOperation.scrape_albums:
        # Proceed with album scraping IR Pipeline.
        pass
    elif operation == ProgramOperation.scrape_songs:
        # Proceed with song scraping IR Pipeline.
        pass
    else:
        print("WS3[main]: Program operation incorrectly specified or not yet implemented.")


if __name__ == '__main__':
    # Instantiate the storage directory relative to this file in the project hierarchy:
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../..', 'Data/OHLA/'
    ))
    # TODO: Create a json file that contains metadata such as resume target and list of failed scraped targets.
    ''' Determine where to resume scraping '''
    # Determine if the metadata targeting file exists:
    scraper_metadata_json = storage_dir + "\\WebScraper\\MetaData\\scraper_metadata.json"
    # Create the metadata file and populate with a list of artists:
    main(operation=ProgramOperation.scrape_albums)
