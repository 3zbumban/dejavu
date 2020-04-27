from __future__ import absolute_import
import binascii
import logging

from sqlalchemy.sql.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, String, Boolean, Binary
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)
Base = declarative_base()
SQLite_MAXS = 950     # maximum of colums in sqlite


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    fingerprinted = Column(Boolean, default=False)
    file_sha1 = Column(Binary(length=20), nullable=False)


class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(Integer, primary_key=True, nullable=False)
    hash = Column(Binary(length=10), nullable=False)
    song_id = Column(
        Integer, ForeignKey(Song.id, ondelete="CASCADE"), nullable=False
    )
    offset = Column(Integer, nullable=False)

    unique = UniqueConstraint('hash', 'song_id', 'offset')


def chunker(l, n=950):
    for i in range(0, len(l), n):
        yield l[i:i+n]


class Database(object):
    def __init__(self, url):
        super(Database, self).__init__()
        self.url = url
        self.engine = create_engine(url)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

        # clean by deleting not fully fingerprinted songs; possibly because of abruptly killed previous run
        self.session.query(Song).filter(Song.fingerprinted.is_(False)).delete()
        self.session.commit()

    def set_song_fingerprinted(self, sid):
        """
        Marks a song as having all fingerprints in the database.

        :param sid: Song identifier
        """
        song = self.session.query(Song).filter(Song.id == sid).one()
        song.fingerprinted = True
        self.session.commit()

    def get_songs(self):
        """Returns all fully fingerprinted songs in the database."""
        return self.session.query(Song).filter(Song.fingerprinted)

    def get_song_by_id(self, sid):
        """
        Return a song by its identifier

        :param sid: Song identifier
        """
        return self.session.query(Song).filter(Song.id == sid).one_or_none()

    def insert_song(self, song_name, file_hash):
        """
        Inserts a song name into the database, returns the new
        identifier of the song.

        :param song_name: name of the song
        :param file_hash: sha1 hex digest of the filename
        """
        song = Song(name=song_name, file_sha1=binascii.unhexlify(file_hash))
        self.session.add(song)
        self.session.commit()
        return song.id

    def insert_hashes(self, sid, hashes):
        """
        Insert a multitude of fingerprints.

        :param sid: Song identifier the fingerprints belong to
        :param hashes: A sequence of tuples in the format (hash, offset)
            hash: Part of a sha1 hash, in hexadecimal format
            offset: Offset this hash was created from/at.
        """
        fingerprints = []
        for hash, offset in set(hashes):
            fingerprints.append(
                Fingerprint(
                    hash=binascii.unhexlify(hash),
                    song_id=sid,
                    offset=int(offset)
                )
            )

        self.session.bulk_save_objects(fingerprints)

    def return_matches(self, hashes):
        """
        Searches the database for pairs of (hash, offset) values.

        :param hashes: A sequence of tuples in the format (hash, offset)
            hash: Part of a sha1 hash, in hexadecimal format
            offset: Offset this hash was created from/at.

        :returns: a sequence of (sid, offset_difference) tuples.\
            sid: Song identifier
            offset_difference: (offset - database_offset)
        """
        # Create a dictionary of hash => offset pairs for later lookups
        mapper = {}
        for hash, offset in hashes:
            mapper[hash.upper()] = offset

        # Get an iterable of all the hashes we need
        values = [binascii.unhexlify(h) for h in mapper.keys()]

        # foo = self.session.query(Fingerprint).filter(Fingerprint.hash.in_(values))
        # make list of lists with contain former values of valoe (maximum 950 per list)
        liste = list(chunker(values, SQLite_MAXS))
        logger.debug("number of lists after devide to 950sets: %s" % liste.__len__())

        for el in liste:    # maximum size of list (el) is 950 due to sqlite
                            # (see: https://www.sqlite.org/limits.html#max_column)
            for fingerprint in self.session.query(Fingerprint).filter(Fingerprint.hash.in_(el)):
                hash = binascii.hexlify(fingerprint.hash).upper().decode('utf-8')
                yield (fingerprint.song_id, fingerprint.offset - mapper[hash])