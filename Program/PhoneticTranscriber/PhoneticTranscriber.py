"""
PhoneticTranscriber.py
Reads plain text song lyrics and performs phonetic transcriptions utilizing the CMU Corpus (nltk).
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
    main -Performs setup operations, reading plaintext files, downloading new corpora, and writing transcriptions.
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
    tokenized_words = re.split(' |\n', plain_text)
    return tokenized_words


if __name__ == '__main__':
    storage_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..', 'Data/'
    ))
    # If the DownloadNewCorpus flag is set; script will execute nltk download manager then terminate.
    main(download_new_corpus=False, storage_dir=storage_dir)
