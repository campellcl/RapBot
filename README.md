# RapBot
Automatic rhyme detection and generation via similarity of phonetic transcriptions.

## Data Retrieval
Data obtained from:
* [Kaggle-LyricsFreak](https://www.kaggle.com/mousehead/songlyrics)
* [Online Hip-Hop Lyrics Archive](http://ohhla.com/all.html)
* [Rap Genius](https://rap.genius.com/)
* List of Hip-Hop Artists via the [Spotify REST API](https://developer.spotify.com/web-api/) and [Spotipy](https://spotipy.readthedocs.io/en/latest/#)
* Discography Wiki Based Website [Discogs](https://www.discogs.com/search/) with developer support via [Discog API](https://www.discogs.com/developers/)
* Another possiblity (unresearched as of yet) [allmusic](http://www.allmusic.com/)

## Data Pre-Processing
* PlainText Tokenization Process
    * Utilizing [Regular Expressions for Tokenizing Text](http://www.nltk.org/book/ch03.html)
    * Understanding [Regular Expressions in Python](https://www.tutorialspoint.com/python/python_reg_expressions.htm)
    * Modifying Regular Expressions to [ignore apostrophes](http://stackoverflow.com/questions/2596893/regex-to-match-words-and-those-with-an-apostrophe)
* Text Normalization
    1. Normalizing text to lowercase
    2. Removing affixes
    3. Stemming the text
    4. Performing Lemmatization

## Deliberations
* Choosing a Grapheme to Phoneme Engine:
    * The Natural Language Toolkit [(NLTK)](nltk.org) Carnegie Mellon University Pronounciation Dictionary [(cmudict Corpus)](http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
    * Automatically Generated IPA Transcription via [eSpeak](https://github.com/rhdunn/espeak)
    * Phonet
* Choosing a Language for Grapheme to Phoneme Transcription
    * The Advanced Research Projects Agency Alphabet [(ARPABET)](https://en.wikipedia.org/wiki/Arpabet)
    * The International Phonetic Alphabet [(IPA)](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet)

## Handling Slang
* General Idea: Create a dictionary of failed transcriptions sorted by occurrence.
* Manually create transcription rules for the most common slang terms.

## Helpful Resources
#### Learning Phonology
* What is a Phoneme?
    * What is a Triphone?
* What is a Grapheme?
* What is the technical term for the ["Pronunciation Spellings"](https://english.stackexchange.com/questions/160499/what-is-the-name-for-pronunciation-spelling) utilized by dictionaries?

#### Choosing a Grapheme to Phoneme Transcriber:
* Stack Overflow Question on [Arpabet Phonetic Transcription in Python](http://stackoverflow.com/questions/11911028/python-arpabet-phonetic-transcription)
* The Grapheme to Phoneme Problem[(The "g2p" Problem)](https://linguistics.stackexchange.com/questions/14784/mapping-graphemes-to-phonemes-in-cmudict)
    * [Phonetisaurus](https://github.com/AdolfVonKleist/Phonetisaurus)

#### Grapheme To Phoneme Transcription via NLTK and Cmudict:
* The Natural Language Toolkit Book [(NLTKBOOK)](http://www.nltk.org/book/)
* pitt.edu [lab on Natural Language Processing via NLTK](http://www.pitt.edu/~naraehan/ling1330/Lab15.html)
* The Natural Language Toolkit (NLTK) [How-To's](http://www.nltk.org/howto/)
* A Gist on [Triphone retrieval via cmudict](https://gist.github.com/ConstantineLignos/1219749)
* Carnegie Mellon University [Speech Center](http://www.speech.cs.cmu.edu/)
* CMUDict wrapper: [PronunDict](https://sourceforge.net/projects/pronundict/)

#### Grapheme to Phoneme Transcription via eSpeak:
* Utilizing [eSpeak via command line](https://sourceforge.net/p/espeak/mailman/message/27487520/)

#### Converting ARPABET to IPA Transcriptions
* StackOverflow on [ARPABET to IPA Translation](https://stackoverflow.com/questions/33111685/convert-arpabet-to-ipa-with-stress) via:
    * [Automatic Syllable Detection](https://stackoverflow.com/questions/405161/detecting-syllables-in-a-word)
* One StackOverflow user's implementation of a [transcription converter](https://github.com/mphilli/English_to_IPA)
* Stanford University resource: [conversion chart between ARPABET and IPA](http://web.stanford.edu/class/linguist238/fig04.01.pdf)
* Wikipedia [ARPABET article with conversion charts](https://en.wikipedia.org/wiki/Arpabet)

#### Web Scraping In Python:
* Dataquest's [Guide to Web Scraping With BeautifulSoup](https://www.dataquest.io/blog/web-scraping-tutorial-python/)
* StackOverflow Post [Using lxml and Xpath](https://stackoverflow.com/questions/11465555/can-we-use-xpath-with-beautifulsoup)
* Xpath and Web Parsing:
    * The W3C Gide to [Using XPath Selectors](https://www.w3schools.com/xml/xpath_syntax.asp)
    * The [lxml.etree Tutorial](http://lxml.de/tutorial.html)
