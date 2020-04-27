from __future__ import absolute_import
from __future__ import print_function
import binascii
import dejavu.decoder as decoder
import logging
import multiprocessing
import os
import traceback
import sys

from dejavu import fingerprint
from dejavu.database import Database
from six.moves import range
from six.moves import zip

logger = logging.getLogger(__name__)


def logging_option(levl=False):
    """
    Logging aktiviren
    :param levl: True => DEBUG mode, else INFO mode, default false
    """
    if levl:
        level = logging.DEBUG
    else:
        level = logging.INFO
    format_s = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    handlers = [logging.FileHandler('debug.log', mode='w'), logging.StreamHandler()]
    logging.basicConfig(level=level, format=format_s, handlers=handlers)


class Dejavu(object):

    CONFIDENCE = 'confidence'
    MATCH_TIME = 'match_time'
    OFFSET = 'offset'

    def __init__(self, dburl, fingerprint_limit=None):
        """
        :param dburl: string, database url as supported by SQLAlchemy. (RFC-1738)
        :param fingerprint_limit: int, number of seconds (from the start of the music file) to fingerprint
        """
        super(Dejavu, self).__init__()
        self.db = Database(dburl)
        self.limit = fingerprint_limit
        self.get_fingerprinted_songs()

    def get_fingerprinted_songs(self):
        # get songs previously indexed
        self.songs = self.db.get_songs()
        self.songhashes_set = set()  # to know which ones we've computed before
        for song in self.songs:
            song_hash = binascii.hexlify(song.file_sha1).upper().decode('utf-8')
            self.songhashes_set.add(song_hash)

    def fingerprint_directory(self, path, extensions, nprocesses=None):
        """
        Function do fingerprint a Diretory
        :param path: Path to dir
        :param extensions: list of extensions [".mp3", ".wav"]
        :param nprocesses: numper of processes default: None, suggestet 5
        :return: None
        """
        # Try to use the maximum amount of processes if not given.
        try:
            nprocesses = nprocesses or multiprocessing.cpu_count()
        except NotImplementedError:
            nprocesses = 1
        else:
            nprocesses = 1 if nprocesses <= 0 else nprocesses

        pool = multiprocessing.Pool(nprocesses)

        filenames_to_fingerprint = []
        for filename, _ in decoder.find_files(path, extensions):
            logger.debug("processing: %s" % filename)
            # don't refingerprint already fingerprinted files
            if decoder.unique_hash(filename) in self.songhashes_set:
                logger.info(
                    "skipping: %s already fingerprinted, continuing..." % filename
                )
                continue

            filenames_to_fingerprint.append(filename)

        # Prepare _fingerprint_worker input
        worker_input = list(
            zip(
                filenames_to_fingerprint,
                [self.limit] * len(filenames_to_fingerprint)
            )
        )

        # Send off our tasks
        iterator = pool.imap_unordered(_fingerprint_worker, worker_input)

        # Loop till we have all of them
        while True:
            try:
                song_name, hashes, file_hash = next(iterator)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                break
            except:
                logger.error("Failed fingerprinting")
                # Print traceback because we can't reraise it here
                traceback.print_exc(file=sys.stdout)
            else:
                sid = self.db.insert_song(song_name, file_hash)

                self.db.insert_hashes(sid, hashes)
                self.db.set_song_fingerprinted(sid)
                self.get_fingerprinted_songs()

        pool.close()
        pool.join()

    def fingerprint_file(self, filepath, song_name=None):
        songname = decoder.path_to_songname(filepath)
        song_hash = decoder.unique_hash(filepath)
        song_name = song_name or songname
        # don't refingerprint already fingerprinted files
        if song_hash in self.songhashes_set:
            logger.info("skipping: %s already fingerprinted, continuing..." % song_name)
        else:
            song_name, hashes, file_hash = _fingerprint_worker(
                filepath, self.limit, song_name=song_name
            )
            sid = self.db.insert_song(song_name, file_hash)

            self.db.insert_hashes(sid, hashes)
            self.db.set_song_fingerprinted(sid)
            self.get_fingerprinted_songs()

    def find_matches(self, samples, Fs=fingerprint.DEFAULT_FS):
        hashes = fingerprint.fingerprint(samples, Fs=Fs)
        return self.db.return_matches(hashes)

    def align_matches(self, matches):
        """
            Finds hash matches that align in time with other matches and finds
            consensus about which hashes are "true" signal from the audio.

            Returns a dictionary with match information.
        """
        # align by diffs
        diff_counter = {}
        largest = 0
        largest_count = 0
        song_id = -1
        for tup in matches:
            sid, diff = tup
            if diff not in diff_counter:
                diff_counter[diff] = {}
            if sid not in diff_counter[diff]:
                diff_counter[diff][sid] = 0
            diff_counter[diff][sid] += 1

            if diff_counter[diff][sid] > largest_count:
                largest = diff
                largest_count = diff_counter[diff][sid]
                song_id = sid

        # extract idenfication
        song = self.db.get_song_by_id(song_id)
        if song:
            songname = song.name
        else:
            return None

        # return match info
        nseconds = round(
            float(largest) / fingerprint.DEFAULT_FS *
            fingerprint.DEFAULT_WINDOW_SIZE * fingerprint.DEFAULT_OVERLAP_RATIO,
            5
        )
        song = {
            'song_id': song_id,
            'song_name': songname,
            Dejavu.CONFIDENCE: largest_count,
            Dejavu.OFFSET: int(largest),
            'offset_seconds': nseconds,
            'file_sha1': binascii.hexlify(song.file_sha1).decode('utf-8'),
        }
        return song

    def recognize(self, recognizer, *options, **kwoptions):
        r = recognizer(self)
        return r.recognize(*options, **kwoptions)

    def print_songs(self, bol=False):
        """
        Method to print out all songs
        :return: List of songs
        """
        liste = []
        for song in self.db.get_songs():
            if bol:
                text = "| id: {:>5} | sha1: {:>12} | name: {:>13}".format(song.id, binascii.hexlify(
                                                                          song.file_sha1).upper().decode('utf-8'),
                                                                          song.name)
                logger.debug(text)
            liste.append(song)
        return liste


def _fingerprint_worker(filename, limit=None, song_name=None):
    # Pool.imap sends arguments as tuples so we have to unpack
    # them ourself.
    try:
        filename, limit = filename
    except ValueError:
        pass

    songname, extension = os.path.splitext(os.path.basename(filename))
    song_name = song_name or songname
    channels, Fs, file_hash = decoder.read(filename, limit)
    result = set()
    channel_amount = len(channels)

    for channeln, channel in enumerate(channels):
        logger.info(
            (
                "Fingerprinting channel %d/%d for %s" %
                (channeln + 1, channel_amount, filename)
            )
        )
        hashes = fingerprint.fingerprint(channel, Fs=Fs)
        logger.info(
            (
                "Finished channel %d/%d for %s" %
                (channeln + 1, channel_amount, filename)
            )
        )
        result |= set(hashes)

    return song_name, result, file_hash


def chunkify(lst, n):
    """
    Splits a list into roughly n equal parts.
    http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
    """
    return [lst[i::n] for i in range(n)]
