import os
import pathlib
from datetime import datetime
import hashlib

import sqlite3

from PIL import Image as PILImage
from PIL import ExifTags
from PIL import TiffImagePlugin


SQL_INIT_SOURCE = '''
CREATE TABLE IF NOT EXISTS source (
  source_id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT,
  path TEXT,
  name TEXT,
  count INTEGER,
  created INTEGER);
'''

SQL_INIT_IMAGE = '''
CREATE TABLE IF NOT EXISTS image (
  image_id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT,
  name TEXT,
  timestamp INTEGER,
  timestamp_via TEXT,
  status TEXT,
  hash TEXT,
  annotation TEXT,
  changed INTEGER,
  exif TEXT,
  source_id INTEGER,
  FOREIGN KEY (source_id) REFERENCES source(source_id)
);'''

class Database(object):
    db_file = ''
    conn = None
    cursor = None

    # PRAGMA table_info('source')
    # PRAGMA table_info('image')

    def __init__(self, db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        self.conn = conn
        self.db_file = db_file
        cursor.execute(SQL_INIT_SOURCE)
        cursor.execute(SQL_INIT_IMAGE)
        self.cursor = cursor

    def exec_sql(self, sql, commit=False):
        #print(sql)
        self.cursor.execute(sql)

        if commit:
            self.conn.commit()
        return self.cursor.lastrowid

    def fetch_sql_all(self, sql):
        rows = []
        for r in self.cursor.execute(sql):
            rows.append(r)
        return rows

    def fetch_sql(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class ClamImage(object):
    exif = None
    entity = None
    pil_handle = None

    def __init__(self, path):
        entity = pathlib.Path(path)
        self.entity = entity
        im = PILImage.open(path)
        self.pil_handle = im
        self.exif = self.get_exif()

    def get_exif(self):
        exif = {}
        tags = ExifTags.TAGS
        for k, v in self.pil_handle._getexif().items():
            if k in tags:
                t = tags[k]
                if (t in ['MakerNote', 'PrintImageMatching']):
                    # massy binary
                    pass
                elif isinstance(v,int) or isinstance(v, str):
                    exif[t] = v
                elif isinstance(v, TiffImagePlugin.IFDRational):
                    #print ('---------', v.denominator, v.numerator)
                    exif[tags[k]] = str(v)
                elif isinstance(v, bytes):
                    exif[tags[k]] = v.decode('ascii')
        return exif

    def get_stat(self):
        return self.entity.stat()

    def make_hash(self, path):
        with open(path, 'rb') as file:
            while True:
                # Reading is buffered, so we can read smaller chunks.
                chunk = file.read(h.block_size)
                if not chunk:
                    break
                h.update(chunk)

        return h.hexdigest()
