#!/usr/bin/python

import os
import sys
import warnings
import argparse
import logging

from dejavu.dejavu import Dejavu, logging_option
from dejavu.recognize import FileRecognizer
from dejavu.recognize import MicrophoneRecognizer
from argparse import RawTextHelpFormatter

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def main():
    logging_option(True)
    parser = argparse.ArgumentParser(
        description="Dejavu: Audio Fingerprinting library",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(   # databse url
        '-d',
        '--dburl',
        nargs='?',
        default="sqlite:///test.db",
        help='Database URL to use. As supported by SQLAlchemy (RFC-1738). '
             'Will read $DATABASE_URL env var if not specified\n'
             'Usages: \n'
             '--dburl sqlite:///test.db\n'
    )
    parser.add_argument(    # dir to fingerprint
        '-f',
        '--fingerprint',
        nargs='*',
        help='Fingerprint files in a directory\n'
             'Usages: \n'
             '--fingerprint /path/to/directory extension\n'
             '--fingerprint /path/to/directory'
    )
    parser.add_argument(    # recognize methods
        '-r',
        '--recognize',
        nargs=2,
        help='Recognize what is playing through the microphone\n'
             'Usage: \n'
             '--recognize mic number_of_seconds \n'
             '--recognize file path/to/file \n'
    )
    parser.add_argument(
        '-l',
        '--limit',
        nargs='?',
        default=None,
        help='Number of seconds from the start of the music files to limit fingerprinting to.\n'
             'Usage: \n'
             '--limit number_of_seconds \n'
    )
    args = parser.parse_args()

    if not args.dburl:
        args.dburl = os.environ['DATABASE_URL']

    if not args.fingerprint and not args.recognize:
        parser.print_help()
        sys.exit(0)

    djv = Dejavu(dburl=args.dburl, fingerprint_limit=args.limit)
    if args.fingerprint:
        # Fingerprint all files in a directory
        if len(args.fingerprint) == 2:   # TODO mehrere extensions, change arparse
            directory = args.fingerprint[0]
            extension = args.fingerprint[1]
            logger.info(
                "Fingerprinting all .%s files in the %s directory" %
                (extension, directory)
            )
            djv.fingerprint_directory(directory, ["." + extension], 4)

        elif len(args.fingerprint) == 1:
            filepath = args.fingerprint[0]
            if os.path.isdir(filepath):
                logger.info(
                    "Please specify an extension if you'd like to fingerprint a directory!"
                )
                sys.exit(1)
            djv.fingerprint_file(filepath)

    elif args.recognize:
        # Recognize audio source
        song = None
        source = args.recognize[0]
        opt_arg = args.recognize[1]

        if source in ('mic', 'microphone'):
            song = djv.recognize(MicrophoneRecognizer, seconds=opt_arg)
        elif source == 'file':
            song = djv.recognize(FileRecognizer, opt_arg)
        print(song)

    sys.exit(0)


if __name__ == '__main__':
    main()
