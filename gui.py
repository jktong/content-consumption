import os
import sys
import time
import nltk ## todo: this is sketch

from PyQt4.QtCore import * 
from PyQt4.QtGui import * 

from managers import CEO
from config import IS_KEYLOGGER, USER_FOLDER
from utils import *

## todo: figure out where this should go
font = QFont('Courier', 12, QFont.Light)

def main():
    app = QApplication(sys.argv) 
    w = MainWindow() 
    w.show()

    sys.exit(app.exec_()) 

def is_keylogger():
    """
    Returns True if we are keylogging in order to offer suggestions (Windows-only)
    """
    return os.name == 'nt' and IS_KEYLOGGER
    

def input_box():
    """
    Returns an input box that raises a QT SIGNAL
    in response to the space bar
    """
    inp = SpacebarTextEdit()
    inp.setFont(font)
    return inp

def btn(init_text='-'):
    return QPushButton(init_text)

def lbl(init_text='-'):
    return QLabel(init_text)

def output_box():
    out = QTextEdit()
    out.setReadOnly(True)
    out.setAcceptRichText(True)
    out.setFont(font)
    return out

def output_line():
    out = QLineEdit()
    out.setReadOnly(True)
    out.setFont(font)
    return out

def output_word():
    return lbl()

def output_grid(entries):
    """
    Takes an iterable of tuple-pairs and returns a grid layout
    """
    grid = QGridLayout()
    for i, (a, b) in enumerate(entries):
        grid.addWidget(a, i, 0)
        grid.addWidget(b, i, 1)
    return grid

def update_grid(grid, entries):
    """
    Takes an iterable of tuple-pairs and updates a grid layout
    """
    for i, (a, b) in enumerate(entries):
        grid.itemAtPosition(i, 0).widget().setText(str(a))
        grid.itemAtPosition(i, 1).widget().setText(str(b))


def vstack_widgets(widgets, with_stretch=False):
    """
    Returns a layout that vertically stacks the given widgets
    """
    layout = QVBoxLayout()
    for i, w in enumerate(widgets):
        if isinstance(w, QWidget):
            layout.addWidget(w)
        elif isinstance(w, QLayout):
            layout.addLayout(w)
        else:
            raise NotImplementedError('Tried to add unknown type %s to layout' % type(w))
            
        if with_stretch and i%2==1:
            ## assumes that widgets are paired when adding stretches
            layout.addStretch(1)

    return layout


def health_widget():
    entries = [ (lbl(corpus_name), lbl()) for corpus_name in get_corpora().keys()]
    return output_grid(entries)


class MainWindow(QWidget): 

    def __init__(self, *args):
        
        QWidget.__init__(self, *args)

        ## attributes
        self.input = input_box()
        self.grep_widget = output_box()
        self.generative_text = output_box()
        self.synonyms = output_line()
        self.user_notifications = lbl('')

        self.update_time = output_word()
        self.last_word = output_word()
        self.corpora_health = health_widget()

        self.time_grep = lbl()
        self.time_generative = lbl()
        self.time_synonyms = lbl()

        self.save_button = btn('Save as corpus')

        ## load the CEO for interacting with corpora
        ceo = CEO()

        # create window
        self.setGeometry(40, 40, 1000, 800)
        self.build_window()

        ## make connections to register signals
        self.register_events()
        
    def build_window(self):
        # build sublayouts
        wide_widgets = [lbl('Write here'),
                        self.input,
                        lbl('Suggestions'),
                        self.time_grep,
                        self.grep_widget,
                        lbl('Synonyms'),
                        self.time_synonyms,
                        self.synonyms,
                        lbl('Generative text'),
                        self.time_generative,
                        self.generative_text,
                        self.user_notifications,
                        ]
        self.wide_layout = vstack_widgets(wide_widgets)

        narrow_widgets = [lbl('Update time'),
                          self.update_time,
                          lbl('Last_word'),
                          self.last_word,
                          lbl('Corpora being used'),
                          self.corpora_health,
                          self.save_button,
                          ]
        self.narrow_layout = vstack_widgets(narrow_widgets, with_stretch=True)

        ## build main layout
        layout = QHBoxLayout()
        layout.addLayout(self.wide_layout)
        layout.addLayout(self.narrow_layout)
        self.setLayout(layout)
        
    def register_events(self):
        """
        Registers QT signal so that 'update' function is called after the user enters a word
        """
        if is_keylogger(): 
            from keylogger import WindowsKeyLogger
            self.sniffer = WindowsKeyLogger()
            self.connect(self.sniffer, SIGNAL('SPACE_PRESSED'),
                         self.update)
        else:
            self.connect(self.input, SIGNAL('SPACE_PRESSED'),
                         self.update)


        self.save_button.clicked.connect(self.save_as_corpus)

    def name_new_corpus(self):
        ## today's date and time
        date_time = get_datetime_as_str()

        ## with what corpora it was based from?
        get_corpora_names = wrap(CEO.get_corpora_names())

        return date_time + ' ' + get_corpora_names + '.txt'

    def save_as_corpus(self):
        """
        Saves user input as a corpus that can be hit upon in the future
        """
        corpus_name = self.name_new_corpus()
        corpus_path = os.path.join(USER_FOLDER, corpus_name)
        with open(corpus_path, 'w') as f:
            f.write(self.input.toPlainText())

        ## notify the user that this was a success
        self.notify_user('New corpus generated!')

    def notify_user(self, text):
        """
        Notify the user unobtrusively. Notice dissapears upon update
        """
        self.user_notifications.setText(text)

    def get_last_word(self):
        """
        Identifies the last word from either the Windows keylogger or the GUI element
        """
        if is_keylogger():
            last_word = self.sniffer.read_buffer()
            self.sniffer.clear_buffer()
        else:
            tokens = nltk.wordpunct_tokenize(self.input.toPlainText())
            words = [str(t) for t in tokens if str(t).isalpha()]
            last_word = words[-1] if len(words) > 0 else None

        return last_word
        
    def update(self):
        """
        Called after user finishes typing a word
        """
        t1 = time.time()
        word = self.get_last_word()

        if word:
            self.update_last_word_widget(word)
            self.update_grep_widget(word)
            self.update_synonyms_widget(word)
            self.update_generative_text_widget(word)
            self.update_corpora_health_widget(word)
       
        t2 = time.time()
        time_taken = (t2-t1)*1000.0
        self.update_time.setText('%0.3f ms' % time_taken)

        ## clear leftover notifications
        self.user_notifications.setText('')


    def update_last_word_widget(self, word):
        """
        Update the last_word widget
        """
        self.last_word.setText(word)
        
    def update_grep_widget(self, word):
        """
        Update the suggestions widget if there are results
        """
        t1 = time.time()

        corpus_output = CEO.grep(word)
        if corpus_output:
            self.grep_widget.setHtml(corpus_output)

        t2 = time.time()
        time_taken = (t2-t1)*1000.0
        self.time_grep.setText('%0.3f ms' % time_taken)
                
    def update_corpora_health_widget(self, word):
        """
        Update the corpora health widget if there are results
        """
        CEO.update_corpora_health(word)
        corpora_health = CEO.get_corpora_health()
        if corpora_health:
            update_grid(self.corpora_health, corpora_health)

    def update_synonyms_widget(self, word):
        t1 = time.time()

        synonyms = CEO.synonyms(word)
        if synonyms:
            self.synonyms.setText(synonyms)

        t2 = time.time()
        time_taken = (t2-t1)*1000.0
        self.time_synonyms.setText('%0.3f ms' % time_taken)
            
    def update_generative_text_widget(self, word):
        t1 = time.time()

        generative_text = CEO.generate([word,])
        if generative_text:
            self.generative_text.setText(generative_text)

        t2 = time.time()
        time_taken = (t2-t1)*1000.0
        self.time_generative.setText('%0.3f ms' % time_taken)
            
class SpacebarTextEdit(QTextEdit):
    """
    An input box that raises a QT SIGNAL in response to the space bar
    """
    def __init__(self, *args):
        QTextEdit.__init__(self, *args)
        
    def event(self, event):
        if (event.type()==QEvent.KeyPress) and (event.key()==Qt.Key_Space):
            self.emit(SIGNAL('SPACE_PRESSED')) 

        return QTextEdit.event(self, event)

        
if __name__ == "__main__": 
    main()

######## RELATED WORDS STUFF #########
#### this is backwards looking.... so it doesn't work very well 
###        related_words = Library.related_words(last_word)
##        related_words = Library.synonyms(last_word)
##        if related_words: self.synonyms.setText(related_words)


######## CHUCK WIDGET STUFF #########
##        if not hasattr(self, 'test_widget'):
##            self.test_widget = QLabel('BOOM')
##            self.narrow_layout.addWidget(self.test_widget)
##        else:
##            self.test_widget.hide()

