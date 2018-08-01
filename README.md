# dejavu3

## Purpose
This fork attempts to:
*   [:heavy_check_mark:] Fix bugs with SQLite. 


## Usage

***
**SQlite:** <br>
where <path> is relative: <br>
`engine = create_engine('sqlite:///foo.db')`
[Docs](http://docs.sqlalchemy.org/en/latest/core/engines.html#microsoft-sql-server)
***

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
