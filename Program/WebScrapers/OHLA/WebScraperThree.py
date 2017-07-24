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
from urllib.error import HTTPError
from lxml import etree
import json
import copy

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
        * website_type: A member of class WebsiteType indicating the HTML form of the IR source.
     stage_one: Artist's storage directory has been initialized on the local machine.
     stage_two: Artist's album metadata has been recorded under the artist's directory as album_metadata.json.
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


def scraper_status_decoder(json_dict):
    """
    scraper_status_decoder: This method enables the ScraperStatus Enum to be JSON decodable (read with json.load()).
    :param dict: The dictonary returned by json.load, this method is called only as a hook.
    :return member: The ScraperStatus.member that the provided string actually belongs to.
    :source: https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
    """
    if "__enum__" in json_dict:
        name, member = json_dict["__enum__"].split(".")
        return getattr(ScraperStatus, member)
    else:
        return json_dict


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


class WebsiteType(Enum):
    """
    WebsiteType: An Enumerated type representing the different versions of artist web pages on OHHLA's website.
        remote_ftp: The primary type of artist website (appears to be a simple FTP client).
        table_display: The secondary type of artist website (a series of nested tables on the artist's page).
        unknown: A web configuration unknown to the web scraper, not possible to automate IR without further analysis.
        unavailable: There is no webpage at the specified URL, this artist is useless and should be purged from the
            metadata.
    """
    remote_ftp = 0
    table_display = 1
    unknown = 2
    unavailable = 3


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
                'scrape_status': ScraperStatus.stage_zero
            }
            # Note: A resume_target of (-1, -1) indicates that scraping has not yet resumed for this artist.
            print("WS3[parse_artist_info] Recorded AID: %d, Artist: %s" % (artist_identifier, artist_name))
            # Note: During dictionary instantiation the artist is assigned an IR status of stage_zero.
        except Exception:
            # The artist either has no associated URL or this is just a placeholder HTML tag.
            pass
    return artists


def get_scraper_metadata():
    """
    get_scraper_metadata: Loads the artist metadata stored in scraper_metadata.json into memory.
    :return artists: The artist metadata recorded during ScraperStatus.stage_zero in scraper_metadata.json.
    """
    with open(scraper_metadata_json, 'r') as fp:
        # artists = json.load(fp=fp, object_hook=scraper_status_decoder, object_pairs_hook=OrderedDict)
        artists = json.load(fp=fp, object_hook=scraper_status_decoder)
    # Convert keys from strings back to integers
    artists = {int(k): v for k, v in artists.items()}
    # Convert dictionary back into ordered dictionary:
    artists = OrderedDict(artists)
    return artists


def init_artist_storage_dir(artist_info):
    """
    init_artist_storage_dir: Initializes a storage directory on the local machine for the provided artist if one does
        not already exist. If the directory does exist, no changes are made.
    :param artist_info: All metadata on the artist including:
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
        * website_type: A member of class WebsiteType indicating the HTML form of the IR source.
    :return was_successful: True if the directory specified in artist_info['storage_dir'] was created on the local
        machine (or if it existed already). Otherwise False is returned.
    """
    was_successful = False
    # Check to see if the artist's storage directory exists
    if os.path.isdir(artist_info['storage_dir']):
        '''
        print("WS3[init_artist_storage_dir]: Artist %d (%s) storage dir already exists."
              % (artist_info['aid'], artist_info['name']))
        '''
        was_successful = True
        return was_successful
    else:
        try:
            os.makedirs(artist_info['storage_dir'])
        except OSError as err:
            if type(err) is NotADirectoryError:
                print("WS3[init_artist_storage_dir]: NADE OSError encountered. Exception reads: %s.\nRequesting removal"
                      " of AID: %d (%s) from metadata." % (str(err), artist_info['AID'], artist_info['name']))
                was_successful = False
                return was_successful
            else:
                print("WS3[init_artist_storage_dir]: OSError exception encountered. Exception reads: %s" % str(err))
                was_successful = False
                return was_successful
        print("WS3[init_artist_storage_dir]: Initialized storage dir for artist %d (%s)"
              % (artist_info['AID'], artist_info['name']))
        was_successful = True
        return was_successful


def determine_artist_website_type(artist_info):
    """
    determine_artist_website_type: Determines the type of webpage used to display the provided artist's information.
        The type of the website determines which script to execute for information retrieval. Additionally, the website
        type determines if the artist has any retrievable data (or if their metadata should be expunged from record).
    :param artist_info: Artist metadata (aid, name, url, resume_target, storage_dir, scrape_status):
        * AID: Unique Identifier (integer).
        * name: Artist's name (string).
        * url: The URL for the artists page.
        * resume_target: A tuple (alid, sid) which contains target information for where the WebScraper last left off
            scraping for this particular artist. ALID indicates the unique album identifier, SID indicates the unique
            song identifier associated with the album in question. Scraping is to resume at the specified indices. If
            the resume_target: (-1, -1) then scraping has not started yet for this artist. In the event that the
            resume_target: (None, None) then scraping has been finished for this artist.
        * storage_dir: A string representing the storage directory for the artist relative to the project root.
        * scrape_status: A member of the ScraperStatus class indicating the artist's position in the IR pipeline.
        * website_type: A member of class WebsiteType indicating the HTML form of the IR source.
    :return WebsiteType: An Enumerated constant from the WebsiteType class indicating the HTML structure of the
        artist's url.
    """
    try:
        html_response = urlopen(artist_info['url'])
    except HTTPError as err:
        # The artist's web page was not accessible.
        print("WS3[determine_artist_website_type]: HTTPError; the artist %d (%s) has no "
              "webpage at the provided url: %s. Exception reads: %s"
              % (artist_info['AID'], artist_info['name'], artist_info['url'], str(err)))
        print("WS3[determine_artist_website_type]: Requesting artist %d (%s) be removed from the metadata in memory..."
              % (artist_info['AID'], artist_info['name']))
        return WebsiteType.unavailable
    # Parse the HTML Response:
    html_parser = etree.HTMLParser()
    # Create an lxml tree for xpath extraction:
    tree = etree.parse(html_response, html_parser)
    try:
        # Try the first web design xpath:
        first_anchor = tree.xpath('//body/table/tr/th//a')[0]
        if first_anchor.text == 'Name':
            return WebsiteType.remote_ftp
    except IndexError as err:
        try:
            # Try the second web design xpath:
            table_layout_div = tree.xpath('//body/div[2]/div[2]/div[2]/div[1]')[0]
            if table_layout_div.get('id') == 'leftmain':
                return WebsiteType.table_display
        except IndexError as err:
            # Fallthrough logic:
            return WebsiteType.unknown


def web_scrape_remote_ftp(artist_info):
    """
    web_scrape_remote_ftp: Retrieves the album's metadata at the artist's specified url. Metadata retrieved includes:
        * assoc_aid: The artist's unique identifier (int).
        * alid: The album's unique identifier (int).
        * name: The album's name (string).
        * url: The album's url (string).
        * storage_dir: The album's storage directory on the local machine (string).
        * scraped: A boolean flag indicating whether or not the album has been scraped in its entirety.
    :param artist_info: Artist metadata (aid, name, url, resume_target, storage_dir, scrape_status):
        * AID: Unique Identifier (integer).
        * name: Artist's name (string).
        * url: The URL for the artists page.
        * resume_target: A tuple (alid, sid) which contains target information for where the WebScraper last left off
            scraping for this particular artist. ALID indicates the unique album identifier, SID indicates the unique
            song identifier associated with the album in question. Scraping is to resume at the specified indices. If
            the resume_target: (-1, -1) then scraping has not started yet for this artist. In the event that the
            resume_target: (None, None) then scraping has been finished for this artist.
        * storage_dir: A string representing the storage directory for the artist relative to the project root.
        * scrape_status: A member of the ScraperStatus class indicating the artist's position in the IR pipeline.
        * website_type: A member of class WebsiteType indicating the HTML form of the IR source.
    :return albums: A dictionary of album metadata retrieved from the provided artist url.
    """
    albums = OrderedDict()
    try:
        html_response = urlopen(artist_info['url'])
        # Parse the HTML Response:
        html_parser = etree.HTMLParser()
        # Create an lxml tree for xpath extraction:
        tree = etree.parse(html_response, html_parser)
    except HTTPError as err:
        print("WS3[determine_artist_website_type]: HTTPError; the artist %d (%s) has no "
              "webpage at the provided url: %s. Exception reads: %s. Terminating..."
              % (artist_info['aid'], artist_info['name'], artist_info['url'], str(err)))
        exit(-1)
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
        album_url = artist_info['url'] + album_name
        albums[i] = {
            'assoc_aid': artist_info['AID'],
            'alid': i, 'name': album_name,
            'url': album_url,
            'storage_dir': artist_info['storage_dir'] + "\\" + album_name,
            'scraped': None
        }
    return albums


def web_scrape_table_display(artist_info):
    """
    web_scrape_table_display: Retrieves the album's metadata at the artist's specified url. Metadata retrieved includes:
        * assoc_aid: The artist's unique identifier (int).
        * alid: The album's unique identifier (int).
        * name: The album's name (string).
        * url: The album's url (string).
        * storage_dir: The album's storage directory on the local machine (string).
        * scraped: A boolean flag indicating whether or not the album has been scraped in its entirety.
    :param artist_info: Artist metadata (aid, name, url, resume_target, storage_dir, scrape_status):
        * AID: Unique Identifier (integer).
        * name: Artist's name (string).
        * url: The URL for the artists page.
        * resume_target: A tuple (alid, sid) which contains target information for where the WebScraper last left off
            scraping for this particular artist. ALID indicates the unique album identifier, SID indicates the unique
            song identifier associated with the album in question. Scraping is to resume at the specified indices. If
            the resume_target: (-1, -1) then scraping has not started yet for this artist. In the event that the
            resume_target: (None, None) then scraping has been finished for this artist.
        * storage_dir: A string representing the storage directory for the artist relative to the project root.
        * scrape_status: A member of the ScraperStatus class indicating the artist's position in the IR pipeline.
        * website_type: A member of class WebsiteType indicating the HTML form of the IR source.
    :return albums: A dictionary of album metadata retrieved from the provided artist url.
    """
    try:
        html_response = urlopen(artist_info['url'])
    except HTTPError as err:
        # The artist's web page was not accessible.
        print("WS3[web_scrape_table_display]: HTTPError; the artist %d (%s) has no "
              "webpage at the provided url: %s. Exception reads: %s"
              % (artist_info['aid'], artist_info['name'], artist_info['url'], str(err)))
    # Parse the HTML Response:
    html_parser = etree.HTMLParser()
    # Create an lxml tree for xpath extraction:
    tree = etree.parse(html_response, html_parser)
    albums_xpath = tree.xpath('//body/div[2]/div[2]/div[2]/div[1]/table/tr[2]/td/p[1]/table/tr/th')
    # TODO: Figure out how to use lxml to select the content.
    print("WS3[web_scrape_table_display]: LXML Error; failure to parse invalid HTML. Requesting artist "
          "AID: %d (%s) be removed from the metadata" % (artist_info['AID'], artist_info['name']))
    return None


def web_scrape_albums(artist_info):
    """
    web_scrape_albums: Retrieves the album's metadata at the artist's specified url. Metadata retrieved includes:
        * assoc_aid: The artist's unique identifier (int).
        * alid: The album's unique identifier (int).
        * name: The album's name (string).
        * url: The album's url (string).
        * storage_dir: The album's storage directory on the local machine (string).
        * scraped: A boolean flag indicating whether or not the album has been scraped in its entirety.
    :param artist_info:
    :return albums:
    """
    albums = OrderedDict()
    website_type = determine_artist_website_type(artist_info)
    if website_type == WebsiteType.remote_ftp:
        albums = web_scrape_remote_ftp(artist_info)
    elif website_type == WebsiteType.table_display:
        albums = web_scrape_table_display(artist_info)
    elif website_type == WebsiteType.unknown:
        # TODO: Record data for analysis about why the website failed to be identified.
        print("WS3[web_scrape_albums]: The specified website (%s) for AID: %d (%s) has an HTML format foreign to"
              " the WebScraper." % (artist_info['url'], artist_info['AID'], artist_info['name']))
    elif website_type is None:
        pass
    else:
        # Error that should never happen.
        pass
    return albums


def remove_artist_from_metadata(artists, aid):
    """
    remove_artist_from_metadata: Removes the artist with the specified AID from memory and updates key indices.
    :param artists:
    :param aid:
    :return:
    """
    updated_artists = OrderedDict()
    index = 0
    for AID, artist_info in artists.items():
        if AID != aid:
            updated_artists[index] = artist_info
            index += 1
    # Update the AID fields in artist_info
    for AID, artist_info in updated_artists.items():
        updated_artists[AID]['AID'] = AID
    '''
    for AID, artist_info in artists.items():
        if AID >= aid and AID < len(updated_artists) - 1:
            updated_artists[AID] = artists[AID + 1]
    '''
    return updated_artists


def update_artist_metadata_on_hdd(artists):
    """
    update_artist_metadata_on_hdd: Updates the artist's metadata ('scraper_metadata.json') on the local machine.
    :param artists: The dictionary of artists and their associated metadata.
    :return None: Upon completion, the json file 'scraper_metadata.json' will be updated with the provided dict.
    """
    with open(scraper_metadata_json, 'w') as fp:
        json.dump(artists, fp, indent=4, cls=ScraperStatusEncoder)


def scrape_artists():
    """
    scrape_artists: Helper method for main, handles the scraping of artist metadata and the creation of the metadata
        file 'scraper_metadata.json'.
    :return None: Upon completion; the metadata file 'scraper_metadata.json' will be created with identifying artist
     information.
    """
    ''' Proceed with artist scraping IR Pipeline. '''
    print("WS3[scrape_artists]: Program started with directive: SCRAPE_ARTISTS")
    # Check to see if the file containing metadata exists:
    if file_exists(scraper_metadata_json):
        print("WS3[scrape_artists]: The file 'scraper_metadata.json' already exists. Artist info has already been retrieved."
              " To reinitialize the metadata file delete 'scraper_metadata.json' and run the program again.")
    else:
        print("WS3[scrape_artists]: The metadata file: 'scraper_metadata.json' was not found. Reinitializing metadata via"
              " artist web scraper.")
        artists = web_scrape_artists()
        print("WS3[scrape_artists]: Artist information retrieved. "
              "There were %d artists retrieved successfully. Writing to HDD..." % len(artists))
        update_artist_metadata_on_hdd(artists=artists)
        print("WS3[scrape_artists]: Artist metadata stored on the HDD, stage_zero of Artist IR Pipeline "
              "complete for all artists.")
        print("WS3[scrape_artists]: Initializing storage directories for all artists on the local machine:")
        init_artists_storage_dirs(artists=artists, resume_aid=0)
        print("WS3[scrape_artists]: Done; directories initialized for every possible artist on the local machine. "
              "Exiting with success!")
        exit(0)


def init_artists_storage_dirs(artists, resume_aid):
    """
    init_artists_storage_dirs: Initializes storage directories on the local machine for all artists in the provided
        'artists' dictionary, beginning at the specified resume_aid.
    :param artists: The artist metadata contained in 'scraper_metadata.json' and loaded into memory by the
        helper function: 'get_scraper_metadata'.
    :param resume_aid: The specified unique artist identifier to resume directory instantiation at.
    :return:
    """
    finished = False
    control_interrupt = (False, None)
    while not finished:
        for aid, artist_info in artists.items():
            if artist_info['scrape_status'] == ScraperStatus.stage_zero:
                # Attempt to create a new storage directory for the artist (it doesn't already exist):
                success = init_artist_storage_dir(artist_info)
                if success:
                    artists[aid]['scrape_status'] = ScraperStatus.stage_one
                    print("\tWS3[init_artists_storage_dirs]: Local directory initialized for AID %d (%s). "
                          "Artist's IR pipeline status updated to stage_one." % (aid, artist_info['name']))
                else:
                    # Failure to initialize artist storage directory.
                    print("\tWS3[init_artists_storage_dirs]: Failure to initialize local directory for AID %d (%s). "
                          "Requesting that this artist be removed from the metadata..." % (aid, artist_info['name']))
                    control_interrupt = (True, aid)
                    break
        if control_interrupt[0]:
            # An artist interrupted the IR pipeline with a failure to create a local storage directory.
            artists = remove_artist_from_metadata(artists=artists, aid=control_interrupt[1])
            print("WS3[scrape_artists]: Control loop recognized request for deletion; artist removed. "
                  "Re-attempting to initialize storage directories without this artist:")
            control_interrupt = (False, None)
        else:
            update_artist_metadata_on_hdd(artists)
            print("\tWS3[init_artists_storage_dirs]: Completed! All artist's now at stage_one in the IR Pipeline. "
                  "Updated metadata on local machine.")
            return


def scrape_albums():
    """
    scrape_albums: Helper method for main, handles the scraping of album metadata and the creation of the appropriate
        album subdirectories.
    :return None: Upon completion
    """
    ''' Proceed with album scraping IR Pipeline '''
    print("WS3[main]: Program started with directive: SCRAPE_ALBUMS\nLoading WebScraper MetaData...")
    # Load metadata:
    artists = get_scraper_metadata()
    print("WS3[main]: Data loaded. Resuming album scraping IR pipeline. Initializing artists' local "
          "storage directories.")
    # Create local storage directories for artist and update scraper status
    for aid, artist_info in artists.items():
        if artist_info['scrape_status'] != ScraperStatus.stage_three:
            # Attempt to create a new storage directory for the artist if it doesn't already exist:
            was_successful = init_artist_storage_dir(artist_info)
            if not was_successful:
                # If the attempt to create the directory was unsuccessful (invalid dir name), then modify the dict:
                control_interrupt = (True, aid)
                break
            else:
                artists[aid]['scrape_status'] = ScraperStatus.stage_one
                print("WS3[main]: Updated Artist AID: %d (%s) IR pipeline status to stage_one."
                      % (artist_info['AID'], artist_info['name']))
                albums = web_scrape_albums(artist_info)
                # Check to see if the artist had any albums to retrieve:
                if albums is not None:
                    print("WS3[main]: Artist's metadata scraped for albums:")
                    for alid, album_info in albums.items():
                        print("\tWS3[main]: ALID: %d (%s)" % (alid, album_info['name']))
                    with open(artist_info['storage_dir'] + "\\album_metadata.json", 'w') as fp:
                        json.dump(fp=fp, obj=albums, indent=4)
                    artists[aid]['scrape_status'] = ScraperStatus.stage_two
                    print("WS3[main]: Artist metadata written to hard drive. "
                          "Updated Artist's IR pipeline status to stage_two.")
                    for alid, album_info in albums.items():
                        if os.path.isdir(album_info['storage_dir']):
                            artists[album_info['assoc_aid']]['scrape_status'] = ScraperStatus.stage_three
                        else:
                            try:
                                os.makedirs(album_info['storage_dir'])
                                artists[album_info['assoc_aid']]['scrape_status'] = ScraperStatus.stage_three
                            except OSError as err:
                                print("WS3[main]: Error attempting to initialize album storage directory on local machine. "
                                      "Exception reads:\n\t%s" % str(err))
                    print("WS3[main]: Album directories initialized on local machine. Updated artist's IR pipeline status"
                          " to stage_three.")
                    with open(scraper_metadata_json, 'w') as fp:
                        json.dump(artists, fp, indent=4, cls=ScraperStatusEncoder)
                    print("WS3[main]: Artist album metadata IR task completed successfully. Updated artist metadata on local "
                          "machine.")
                else:
                    # The artist had no albums to scrape, remove them from the metadata.
                    # TODO: Modify code so no dictionary removal is happening during iteration
                    artists = remove_artist_from_metadata(artists, artist_info['AID'])
                    print("WS3[main]: Control loop recognized the request for artist removal. Removed artist from memory.")
                    # Update the representation on the hard drive:
                    with open(scraper_metadata_json, 'w') as fp:
                        json.dump(fp=fp, obj=artists, indent=4, cls=ScraperStatusEncoder)
                    print("WS3[main]: Updated the artist metadata on the local machine")
        else:
            print("WS3[main]: Artist %d (%s) already at stage three in the IR Pipeline. "
                  "Proceeding to next artist." % (artist_info['AID'], artist_info['name']))
    # If the control loop was interrupted due to a requested modification to the artists's dictionary:
    if control_interrupt[0]:
        artists = remove_artist_from_metadata(artists=artists, aid=control_interrupt[1])


def main(operation):
    if operation == ProgramOperation.scrape_artists:
        scrape_artists()
    elif operation == ProgramOperation.scrape_albums:
        scrape_albums()
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
    main(operation=ProgramOperation.scrape_artists)
