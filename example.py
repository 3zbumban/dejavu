from __future__ import absolute_import
from __future__ import print_function

import os
import warnings
import logging

from dejavu.dejavu import Dejavu, logging_option
from dejavu.recognize import FileRecognizer    # , MicrophoneRecognizer

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    logging_option(True)
    dburl = os.getenv('DATABASE_URL', 'sqlite:///test.db')
    logger.debug(dburl)
    djv = Dejavu(dburl=dburl)

    # Fingerprint all the mp3's in the directory we give it
    djv.fingerprint_directory("mp3", [".mp3", ".wav"], 10)
    # Recognize audio from a file
    song = djv.recognize(
        FileRecognizer, "I:\\...\\...\\...\\....wav"
    )
    print("From file we recognized: %s\n" % song)

    # Or recognize audio from your microphone for `secs` seconds
    #secs = 5
    #song = djv.recognize(MicrophoneRecognizer, seconds=secs)
    #if song is None:
    #    print(
    #        "Nothing recognized -- did you play the song out loud so your mic could hear it? :)"
    #    )
    #else:
    #    print("From mic with %d seconds we recognized: %s\n" % (secs, song))

    # Or use a recognizer without the shortcut, in anyway you would like
    recognizer = FileRecognizer(djv)
    song = recognizer.recognize_file(
        "I:\\...\\...\\...\\....wav"
    )
    print("No shortcut, we recognized: %s\n" % song)