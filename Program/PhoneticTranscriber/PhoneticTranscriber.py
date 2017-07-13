"""
PhoneticTranscriber.py
Reads ASCII plain text song lyrics and performs phonetic transcriptions utilizing the CMU Corpus (nltk).
"""
import sys
import os.path
import re
import nltk
import json
from nltk.corpus import cmudict
from enum import Enum
from collections import OrderedDict

__author__ = "Chris Campell"
__created__ = "4/21/2017"
__version__ = "7/06/2017"


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


def transcribe_arpabet_via_cmu(tokenized_words):
    """
    transcribe_arpabet_via_cmu -Performs a Grapheme to Phoneme (G2P) transcription in
        ARPABET utilizing the NLTK in conjunction with the Carnegie Mellon Pronunciation Dictionary (cmudict).
    :param tokenized_words: A list of normalized word-level tokens to be phonetically transcribed.
    :return arpabet_graphones: The ARPABET G2P phonetic transcriptions found in the cmudict.
    :return failed_transcriptions: The list of provided tokens that could not be mapped to the cmudict.
    """
    arpabet_graphones = []
    failed_transcriptions = {}
    # Instantiate pronunciation dictionary prior to iteration to avoid re-instantiation.
    pron_dict = cmudict.dict()
    for line in tokenized_words:
        for token in line:
            token_in_cmudict = False
            for word, phonemes in pron_dict.items():
                if word == token:
                    arpabet_graphones.append((word, phonemes))
                    # print("Token '%s' found in cmudict." % token)
                    token_in_cmudict = True
                    break
            if not token_in_cmudict:
                # print("Token: '%s' not found in cmudict" % token)
                # Check to see if the token already exists as a failed transcription:
                if token in failed_transcriptions:
                    failed_transcriptions[token] += 1
                else:
                    failed_transcriptions[token] = 1
    return arpabet_graphones, failed_transcriptions


def identify_chorus_lines(tokenized_lines_with_spaces):
    """
    identify_chorus_lines: Given a list of plaintext lines in a song (with deliminating '' still present), this method
    will locate the section of the song that constitutes the chorus and return it.
    :param tokenized_lines_with_spaces: A list of plaintext lyrics deliminated by \n character with "" still present as
        sometimes the only way to identify the end of the chorus is via blank spaces "".
    :return chorus: An OrderedDictionary that represents the lines in the song (and their associated line numbers in
        the provided 'tokenized_lines_with_spaces'). Takes the form:
         :key line_num: An index corresponding to the line in the provided list.
         :value line: The plaintext/lyrics in the list corresponding to the line_number.
    """
    chorus = OrderedDict()
    # As far as I can tell songs will mark the end of the chorus based on '' or [Verse #]:
    chorus_start_line_index = None
    chorus_end_line_index = None
    for line_num, line in enumerate(tokenized_lines_with_spaces):
        normalized_line = str.lower(line)
        # Identify the line number that indicates the start of the chorus:
        if 'chorus' in normalized_line:
            chorus_start_line_index = line_num + 1
            break
    # Identify the line number that indicates the end of the chorus:
    if chorus_start_line_index is not None:
        for line_num, line in enumerate(tokenized_lines_with_spaces[chorus_start_line_index:]):
            normalized_line = str.lower(line)
            # The next '' or [] following the chorus marks the end of the chorus:
            regex = re.compile(r'\[(.*)\]')
            if regex.search(normalized_line) or normalized_line == '':
                chorus_end_line_index = line_num + chorus_start_line_index
                break
    else:
        # There is no chorus in the song, just return.
        return tokenized_lines_with_spaces
    # Capture the text that constitutes the chorus:
    line_num = chorus_start_line_index
    for chorus_line in tokenized_lines_with_spaces[chorus_start_line_index:chorus_end_line_index]:
        chorus[line_num] = chorus_line
        line_num += 1
    return chorus


def tokenize_words(line_deliminated_lyrics):
    """
    tokenize_words -Accepts the lyrics of a song as a list of lines and seperates them into a list of words.
    :param tokenized_lyrics: The list of song lyrics read from plaintext.
    :return tokenized_words: A list of words composed using the provided list of lyrics.
    """
    tokenized_lyrics = []
    # Utilize Regular expression to partition on ' ' and '\n':
    # tokenized_words = re.split(' |\n', plain_text)
    '''
    Regular Expression Reads:
    partition on spaces OR new-line characters and ignore apostrophes
    For more information: http://stackoverflow.com/questions/2596893/regex-to-match-words-and-those-with-an-apostrophe
    '''
    for line_num, line in enumerate(line_deliminated_lyrics):
        # Remove punctuation like: ! and @:
        alphanumeric_line = re.sub('[!@#$]', '', line)
        # Normalize line:
        alphanumeric_line = str.lower(alphanumeric_line)
        #tokenized_words = re.split(pattern=r'\s|\n|,|(?=.*\w)^(\w|\')+$',string=plain_text)
        tokenized_words = re.split(pattern=r'\s|\n|,', string=alphanumeric_line)
        # Remove 'None' tokens:
        tokenized_words = [token for token in tokenized_words if token is not None]
        # Remove '' tokens:
        tokenized_words = [token for token in tokenized_words if token is not '''''']
        # tokenized_words = [token if token is not None else token for token in tokenized_words]
        tokenized_lyrics.append(tokenized_words)
    return tokenized_lyrics


def substitute_chorus(tokenized_lines_with_spaces, chorus):
    """
    substitute_chorus: Accepts the lyrics of a song delimited with newlines (containing empty lines), and the
    pre-extracted chorus. Replaces all '[chorus]' tags in the song with the actual chorus lyrics.
    :param tokenized_lines_with_spaces: A list of plaintext lyrics deliminated by \n character with "" still present as
        sometimes the only way to identify the end of the chorus is via blank spaces "".
    :param chorus: The chorus identified via 'identify_chorus_lines'.
    :return tokenized_lines_with_chorus: The provided tokenized lines with the chorus lyrics now substituted in place
        of the '[chorus]' tag.
    """
    # TODO: Write method body.
    pass


def remove_dj_tag(tokenized_lines):
    """
    remove_dj_tag: Removes the lines in the song following a [DJ] tag (as DJ commentary has no lyrical value).
    :param tokenized_lines: The list of song lyrics delimited by a '\n' character.
    :return dj_cleaned_text: The provided list of song lyrics with the lyrics spoken by the DJ removed.
    """
    dj_start_line_index = None
    dj_end_line_index = None
    # Identify the line number that indicates the start of the [DJ] tag:
    for line_num, line in enumerate(tokenized_lines):
        normalized_line = str.lower(line)
        # Identify the line number that indicates the start of the chorus:
        if '[dj]' in normalized_line:
            dj_start_line_index = line_num
            break
    # Identify the line number that indicates the end of the [DJ] tag:
    if dj_start_line_index is not None:
        for line_num, line in enumerate(tokenized_lines[dj_start_line_index+1:]):
            normalized_line = str.lower(line)
            # Define regex expression to identify a '[' with any number of characters followed by another ']':
            regex = re.compile(r'\[(.*)\]')
            # A line containing the above regex expression is the termination point for the DJ's commentary:
            if regex.search(normalized_line):
                dj_end_line_index = line_num + dj_start_line_index + 1
                break
    else:
        # There is no DJ tag just return the provided text:
        return tokenized_lines
    # Return the text with the specified line range omitted:
    dj_cleaned_text = []
    for line_num, line in enumerate(tokenized_lines):
        if line_num < dj_start_line_index:
            dj_cleaned_text.append(line)
        elif line_num > dj_end_line_index:
            dj_cleaned_text.append(line)
    return dj_cleaned_text


def clean_tokenized_lines(tokenized_lines):
    """
    clean_tokenized_lines: Cleans the provided tokenized lines by removing the following tags:
        * [DJ]: Removes any following lines after a [DJ] tag as this content is not reflective of the actual song
            lyrics.
        * [* ACTION *]: Removes any tags containing an action such as 'Applause' which is not reflective of the actual
            lyrical content.
        * [Verse X]: Removes any tags containing verse information so as not to be mistaken as a feature.
    Additionally, this method removes any background commentary denoted in the lyrics by (text text text).
    :param tokenized_lines: The list of ascii lyrics broken into lines.
    :return cleaned_tokenized_lines: The provided tokenized_lines now cleaned by removing the tags specified above.
    """
    tokenized_lines = remove_dj_tag(tokenized_lines)
    cleaned_tokenized_lines = []
    for line_num, line in enumerate(tokenized_lines):
        normalized_line = str.lower(line)
        # Remove any parentheses indicating commentary:
        normalized_line = re.sub(r'\(.*\)', '', normalized_line)
        # Specify regex to remove all lines containing '[', any number of characters, then ']':
        regex = re.compile(r'\[(.*)\]')
        # Only add lines that contain no text wrapped in square brackets:
        if not regex.search(normalized_line):
            cleaned_tokenized_lines.append(normalized_line)
    return cleaned_tokenized_lines


def repeat_specified_lines(tokenized_lines):
    """
    repeat_specified_lines: Identifies lines in the song lyrics that contain a ascii instruction to duplicate the line.
    Lines that contain such commands (often expressed as xN to indicate the preceding line should be repeated N times),
    should be duplicated N times so that the symbol matching algorithm can identify same-rhymes.
    :param tokenized_lines: The list of song lyrics delimited by a '\n' character.
    :return tokenized_lines_with_repeat: The provided song lyrics with lines marked with xN repeated N times.
    """
    tokenized_lines_with_repeat = []
    # Define the regex expression to identify xN:
    regex = re.compile(r'x\d')
    for line_num, line in enumerate(tokenized_lines):
        normalized_line = str.lower(line)
        if not regex.search(normalized_line):
            tokenized_lines_with_repeat.append(line)
        else:
            # The line in question contains instructions to repeat the line 'N' times.
            matched_text = regex.search(normalized_line).group(0)
            num_rep = int(matched_text[len(matched_text) - 1])
            # Remove the repeat instruction from the lyric line:
            line_to_repeat = line.replace(matched_text, '')
            # Repeat the line 'N' times (without repeating the repeat instruction):
            for i in range(num_rep):
                tokenized_lines_with_repeat.append(line_to_repeat)
    return tokenized_lines_with_repeat


def tokenize_lines(plain_text):
    """
    tokenize_lines -Accepts the lyrics of a song as a string and partitions the string into a list of lines.
    :param plain_text: The string containing song lyrics read from plaintext or HTML.
    :return tokenized_lines: A list of lines composed of the provided string deliminated on '\n'
    """
    # Utilize str.split() to partition on '\n' character:
    tokenized_lines = str.split(plain_text, sep='\n')
    ''' Identify the lines in the song that constitute the Chorus '''
    chorus = identify_chorus_lines(tokenized_lines_with_spaces=tokenized_lines)
    ''' Remove empty lines in the song that served previously as Chorus delimiters '''
    tokenized_lines = [line for line in tokenized_lines[5:] if line is not ""]
    ''' Expand lines in the song that contain a specified number of repetitions (for same rhyme identification)'''
    tokenized_lines = repeat_specified_lines(tokenized_lines)
    ''' Clean the lyrics by removing tags ([text]) such as: '[Applause]', '[Chorus]', and '[Verse x]'. '''
    tokenized_lines = clean_tokenized_lines(tokenized_lines)
    return tokenized_lines


def main(download_new_corpus, storage_dir):
    """
    main -Performs Grapheme to Phoneme (G2P) Transcriptions by:
     1. Reading ASCII plaintext files
     2. Downloading new corpora for use by NLTK (if neccessary)
     3. Encoding metadata such as (song name, artist name, album, g2p accuracy, etc...) in JSON form
     4. Writing G2P transcriptions and metadata to output directory in JSON form
    :param download_new_corpus: A boolean flag indicating if a new CMUDict corpus should be fetched from the external
        server.
    :return None: Upon completion, TODO: method header.
    """
    if download_new_corpus:
        nltk.download_gui()
        # Print the paths that NLTK uses for Corpora: print(nltk.data.path)
        sys.exit(0)
    ''' Read Plaintext from Files '''
    for aid, artist_info in target_artists.items():
        print("PT[main]: Parsing PlainText for Artist AID: %d (%s)" % (aid, artist_info['name']))
        for alid, album_info in artist_info['albums'].items():
            print("\tPT[main]: Parsing plaintext for Album ALID: %s (%s)" % (alid, album_info['name']))
            for sid, song_info in album_info['songs'].items():
                print("\t\tPT[main]: Parsing PlainText for SID: %s (%s)" % (sid, song_info['name']))
                song_ascii = song_info['ascii']
                ''' Tokenize Plaintext '''
                # Tokenize Lines:
                tokenized_lines = tokenize_lines(song_ascii)
                # Tokenize Words and Normalize Tokens (convert to lower case):
                tokenized_words = tokenize_words(tokenized_lines)
                # Convert tokenized text to NLTK Text object:
                # tokenized_words = nltk.Text(tokens=tokenized_words)
                ''' Perform Grapheme to Phoneme (G2P) transcription in ARPABET'''
                print("\t\tPT[main]: PlainText tokenized. Performing ARPABET transcription via CMUDict...")
                arpabet_cmu_graphones, failed_transcriptions = transcribe_arpabet_via_cmu(tokenized_words)
                ''' Write G2P Transcription Statistics and Metadata'''
                # Update json encoding of g2p statistics:
                write_dir = song_info['storage_dir'] + "\\transcript_stats.json"
                with open(write_dir, 'w') as fp:
                    json.dump(fp=fp,obj=failed_transcriptions)
                print("\t\tPT[main]: Success. Transcription G2P Statistics Written to HDD under song storage dir.")


if __name__ == '__main__':
    # Initialize storage paths:
    global_storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..', 'Data/'
    ))
    target_artists_loc = global_storage_dir + "\\OHLA\\WebScraper\\MetaData\\target_artists_stage_three.json"
    # Load required target_artists.json into memory:
    print("PT[Init]: Loading artist file into memory (approx. 154 MB) please be patient...")
    target_artists = load_web_scraper_target_urls(target_artists_loc=target_artists_loc)
    # Just do this once:
    update_metadata = True
    if update_metadata:
        print("PT[Init-OneTime]: Performing One-Time update of artist metadata with 'transcribed' flag.")
        ''' Add a boolean 'transcribed' flag to every song '''
        for aid, artist_info in target_artists.items():
            for alid, album_info in artist_info['albums'].items():
                if album_info['songs'] is None:
                    print("PT[Init-OneTime]: Alert! Artist AID %d (%s), ALID %d (%s) has no recorded songs!"
                          % (int(aid), artist_info['name'], int(alid), album_info['name']))
                else:
                    try:
                        for sid, song_info in album_info['songs'].items():
                            if 'transcribed' not in song_info:
                                target_artists[aid]['albums'][alid]['songs'][sid]['transcribed'] = False
                    except AttributeError as err:
                        print("AttributeError while attempting to access album's songs. Error occurred with artist "
                              "AID %d (%s), ALID %d (%s), which has ['songs'] of length: %d"
                              % (int(aid), artist_info['name'], int(alid), album_info['name'], 0))
                        print(str(err))
                        exit(-1)
        ''' Update the representation on the hard drive '''
        with open(target_artists_loc, 'w') as fp:
            json.dump(fp, target_artists, indent=4, cls=EnumEncoder)
        exit(0)
    # TODO: Write modifications to JSON file.
    print("PT[Init]: Metadata loaded into memory. Proceeding to text pre-processing via tokenization.")
    # Note: If the download_new_corpus flag is set; script will execute nltk download manager then terminate.
    main(download_new_corpus=False, storage_dir=global_storage_dir)
