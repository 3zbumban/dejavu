# dejavu

## Purpose

This fork attempts to:
*   [WIP] Support other formats
*   [WIP] Jsonnize
*   [:heavy_check_mark:] Fix bugs (fixes critical numpy one).
*   [:heavy_check_mark:] Use SQLAlchemy to support PostgreSQL, SQLite3 DBs as well.
*   [:heavy_check_mark:] Use Pipenv to allow db credentials via .env file
*   [:heavy_check_mark:] Support both Python3 and Python2.
*   [WIP] Use the logging module so as to not litter any user's application with prints.
*   [:heavy_check_mark:] Reformat code using YAPF (Facebook)

## Usage

1.  Install directly from this repo:

```commandline
pip install -e git+https://github.com/bcollazo/dejavu@v1.2#egg=PyDejavu
```

2.  Import and use:

```python
from dejavu import Dejavu
from dejavu.recognize import FileRecognizer

djv = Dejavu(dburl='sqlite://')
djv.fingerprint_directory('~/Music')
song = djv.recognize(FileRecognizer, 'mp3/Dura--Daddy-Yankee.mp3')
print(song)
```

3.  Can also be used as a CLI tool:

```commandline
export DATABASE_URL=mysql+mysqlconnector://bryan:password@localhost/dejavu
python dejavu.py --fingerprint ~/Music mp3 --limit 30
python dejavu.py --recognize mic 10
python dejavu.py --recognize file sometrack.mp3
```

You can keep the database url saved in an .env file and use pipenv. As
well as specify it via the `--dburl` command line argument.

## Migrating from worldveil/dejavu

If you already have a live database that used to follow worldveil/dejavu
database structure, you'll have to migrate your database
by renaming:

*   `song_id` to `id`
*   `song_name` to `name`

in the `songs` table.
