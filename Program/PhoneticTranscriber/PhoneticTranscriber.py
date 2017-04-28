"""
PhoneticTranscriber.py
Reads ASCII plain text song lyrics and performs phonetic transcriptions utilizing the CMU Corpus (nltk).
"""
import sys
import os.path
import re
import nltk
from nltk.corpus import cmudict

__author__ = "Chris Campell"
__version__ = "4/21/2017"

def main(download_new_corpus, storage_dir):
    """
    main -Performs Grapheme to Phoneme (G2P) Transcriptions by:
     1. Reading ASCII plaintext files
     2. Downloading new corpora for use by NLTK (if neccessary)
     3. Encoding metadata such as (song name, artist name, album, g2p accuracy, etc...) in JSON form
     4. Writing G2P transcriptions and metadata to output directory in JSON form
    :param DownloadNewCorpus:
    :return:
    """
    if download_new_corpus:
        nltk.download_gui()
        # Print the paths that NLTK uses for Corpora: print(nltk.data.path)
        sys.exit(0)
    # Read Plaintext from file:
    # Online HipHop Lyrics Archive PlainText Storage Location:
    plain_text_file = storage_dir + '\\OHLA\\PlainText\\Eric B and Rakim\\Paid in Full.txt'
    with open(plain_text_file, 'r') as fp:
        plain_text = fp.read()
    ''' Tokenize Plaintext '''
    # Tokenize Lines:
    tokenized_lines = tokenize_lines(plain_text)
    # Tokenize Words:
    tokenized_words = tokenize_words(plain_text)
    # Normalize tokens:
    tokenized_words = [word.lower() for word in tokenized_words]
    # Convert tokenized text to NLTK Text object:
    # tokenized_words = nltk.Text(tokens=tokenized_words)
    ''' Perform Grapheme to Phoneme (G2P) transcription '''
    arpabet_cmu_graphones, failed_transcriptions = transcribe_arpabet_via_cmu(tokenized_words)
    ''' Build G2P Transcription Statistics and Metadata'''
    g2p_json_encoding = {}
    # TODO: Obtain song metadata. Obtain g2p transcription statistics.
    ''' Write G2P transcription to storage directory '''
    # TODO: Write converted words to storage directory in json format. Attach transcription statistics.

def transcribe_arpabet_via_cmu(tokenized_words):
    """
    transcribe_arpabet_via_cmu -Performs a Grapheme to Phoneme (G2P) transcription in
        ARPABET utilizing the NLTK in conjunction with the Carnegie Mellon Pronunciation Dictionary (cmudict).
    :param tokenized_words: A list of normalized word-level tokens to be phonetically transcribed.
    :return arpabet_graphones: The ARPABET G2P phonetic transcriptions found in the cmudict.
    :return failed_transcriptions: The list of provided tokens that could not be mapped to the cmudict.
    """
    arpabet_graphones = []
    failed_transcriptions = []
    # Instantiate pronunciation dictionary prior to iteration to avoid re-instantiation.
    pron_dict = cmudict.dict()
    for token in tokenized_words:
        token_in_cmudict = False
        for word, phonemes in pron_dict.items():
            # TODO: Fuzzy string comparison?
            if word == token:
                arpabet_graphones.append((word, phonemes))
                # print("Token '%s' found in cmudict." % token)
                token_in_cmudict = True
        if not token_in_cmudict:
            print("Token: '%s' not found in cmudict" % token)
            failed_transcriptions.append(token)
    return arpabet_graphones, failed_transcriptions

def tokenize_lines(plain_text):
    """
    tokenize_lines -Accepts the lyrics of a song as a string and partitions the string into a list of lines.
    :param plain_text: The string containing song lyrics read from plaintext or HTML.
    :return tokenized_lines: A list of lines composed of the provided string deliminated on '\n'
    """
    # Utilize str.split() to partition on '\n' character:
    tokenized_lines = str.split(plain_text, sep='\n')
    return tokenized_lines

def tokenize_words(plain_text):
    """
    tokenize_words -Accepts the lyrics of a song as a string and partitions the string into a list of words.
    :param plain_text: The string containing song lyrics read from plaintext or HTML.
    :return tokenized_words: A list of words composed using the provided string.
    """
    # Utilize Regular expression to partition on ' ' and '\n':
    # tokenized_words = re.split(' |\n', plain_text)
    '''
    Regular Expression Reads:
    partition on spaces OR new-line characters and ignore apostrophes
    For more information: http://stackoverflow.com/questions/2596893/regex-to-match-words-and-those-with-an-apostrophe
    '''
    #tokenized_words = re.split(pattern=r'\s|\n|,|(?=.*\w)^(\w|\')+$',string=plain_text)
    tokenized_words = re.split(pattern=r'\s|\n|,',string=plain_text)
    # Remove 'None' tokens:
    tokenized_words = [token for token in tokenized_words if token is not None]
    # Remove '' tokens:
    tokenized_words = [token for token in tokenized_words if token is not '''''']
    # tokenized_words = [token if token is not None else token for token in tokenized_words]
    return tokenized_words

if __name__ == '__main__':
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..', 'Data/'
    ))
    # If the DownloadNewCorpus flag is set; script will execute nltk download manager then terminate.
    main(download_new_corpus=False, storage_dir=storage_dir)
