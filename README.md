# RapBot
Automatic rhyme detection and generation via similarity of phonetic transcriptions.

## Data Retrieval
Data obtained from:
* [Kaggle-LyricsFreak](https://www.kaggle.com/mousehead/songlyrics)
* [Online Hip-Hop Lyrics Archive](http://ohhla.com/all.html)
* [Rap Genius](https://rap.genius.com/)
* List of Hip-Hop Artists via the [Spotify REST API](https://developer.spotify.com/web-api/) and [Spotipy](https://spotipy.readthedocs.io/en/latest/#)

## Data Pre-Processing
* TODO
## Deliberations
* Choosing a Grapheme to Phoneme Engine:
    * NLTK Cmudict Corpus
    * eSpeak
    * Phonet
* Choosing a Language for Grapheme to Phoneme Transcription
    * ARPABET
    * IPA

## Helpful Resources
#### Learning Phonology
* What is a Phoneme?
    * What is a Triphone?
* What is a Grapheme?
* What is the technical term for ["Pronunciation Spelling"](https://english.stackexchange.com/questions/160499/what-is-the-name-for-pronunciation-spelling) utilized by dictionaries?

#### Choosing a Grapheme to Phoneme Transcriber:
* Stack Overflow Question on [Arpabet Phonetic Transcription in Python](http://stackoverflow.com/questions/11911028/python-arpabet-phonetic-transcription)
* [Phonetisaurus](https://github.com/AdolfVonKleist/Phonetisaurus)

#### Grapheme To Phoneme Transcription via NLTK and Cmudict:
* The Natural Language Toolkit Book [(NLTKBOOK)](http://www.nltk.org/book/)
* pitt.edu [lab on Natural Language Processing via NLTK](http://www.pitt.edu/~naraehan/ling1330/Lab15.html)
* [NLTK How-Tos](http://www.nltk.org/howto/)
* Gist on [Triphone retrieval via cmudict](https://gist.github.com/ConstantineLignos/1219749)
* Carnegie Mellon University's [Speech Center](http://www.speech.cs.cmu.edu/)


    
