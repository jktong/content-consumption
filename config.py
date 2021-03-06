import nltk

# Whether or not to give suggestions if the user is not typing into the editor
IS_KEYLOGGER = True


## the folder in which user generated corpora should be stored
USER_FOLDER = 'user'

## whether or not to hit upon corpora generated by the user
IS_USING_USER_CORPORA = False


## the folder in which non-nltk text-based corpora should be stored
CORPORA_FOLDER = 'data'

CORPORA = {#'Teddy': 'teddy.txt',
##            'Salinger': 'nine_stories.txt',
##            'Engelbart': '1962paper.txt',
            'Emotion Machine':'emotion_machine.txt',
#            'Emma': nltk.corpus.gutenberg.words('austen-emma.txt'),
#           'Romance': nltk.corpus.brown.sents(categories='romance')
           }

###### add all of brown
##for category in nltk.corpus.brown.categories():
##    corpus_name = category.capitalize()
##    corpus = nltk.corpus.brown.sents(categories=category)
##    CORPORA[corpus_name] = corpus


## for limiting the number of corpuses that get hit upon when the user enters text
## todo: integrate this with dynamic timing and perf adjustments so that it
## doesn't have to be hard coded
MAX_CORPORA = min(len(CORPORA), 3)

### todo: make sure these are not hurting perf when people do 'from config import *'
ENGLISH_DIST = nltk.FreqDist(nltk.corpus.brown.words(categories='news'))
STOP_WORDS = nltk.corpus.stopwords.words('english')

