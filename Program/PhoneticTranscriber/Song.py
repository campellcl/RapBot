"""
Song.py
A class representing an artist's song. Holds plaintext ordinal information, and IPA and ARPABET transcriptions.
"""
__author__ = "Chris Campell"
__version__ = "5/9/2017"

class Song(object):
    plain_text_tokenized_lines = {}

    def __init__(self, plain_text):
        """
        Constructor for objects of type Song. Upon initialization the song's provided plaintext is
            partitioned into lines and each line is assigned a line number in order of occurance from
            top to bottom.
        :param plain_text: The string representation of the song in undeliminated plaintext.
        """
        # Utilize str.split() to partition on '\n' character:
        split_lines = str.split(plain_text, sep='\n')
        # Maintain a counter of the current line and append during iteration.
        for line_num, line in enumerate(split_lines):
            self.plain_text_tokenized_lines[line_num] = line

    def
