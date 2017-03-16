"""
GenreFilterer.py
Takes the raw csv of Hip-Hop lyrics provided by Kaggle and LyricsFreak and
    removes all songs not belonging to the Hip-Hop genre.
"""
__author__ = "Chris Campell"
__version__ = "3/16/2017"

import pandas as pd
import os

def main(input_file_path):
    """
    main -Initializes data container structures, and reads data into memory.
    :param input_file_path: The relative file path of the csv input file.
    :return:
    """
    # Read the csv file into memory:
    lyrics = pd.read_csv(input_file_path)
    # Cannot mine hip-hop data without genre tag. Reccomend abondoning appraoch due to lack of genre metadata.
    pass

if __name__ == '__main__':
    # Get the file path to the input csv file:
    input_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                   '../../../Data/Kaggle-LyricsFreak/Pre-Processing/songdata.csv'))
    main(input_file_path=input_file_path)
