'''
key: {timestamp}:{hash[:6]}
'''

from datetime import datetime
import time
import os
import json
import sqlite3
import hashlib

import base64
import struct
import time
import pathlib

from .helpers import (
    ClamImage,
    Database
)

IGNORE_FILES = ['Thumbs.db', '']
IMAGE_EXTENSIONS = ['.JPG', '.JPEG', '.PNG']

def _check_image_filename(dirent):
    _, fext = os.path.splitext(dirent.path)
    if fext.upper() in IMAGE_EXTENSIONS:
        return True
    return False


class Source(object):
    db = None

    def __init__(self, source_type, name=''):
        if source_type == 'database' and name:
            db = Database(name)
            self.db = db

    def update_image(self, image_id, value):
        kv = value.split('=')
        put = '{}="{}"'.format(kv[0], kv[1])
        sql = 'UPDATE image SET {} WHERE image_id={}'.format(put, image_id)
        self.db.exec_sql(sql, True)

    def get_source(self, source_id='', with_image=False):
        if source_id == '' or source_id == '0':
            return self.db.fetch_sql_all('SELECT * FROM source')
        else:
            res = self.db.fetch_sql('SELECT * FROM source WHERE source_id={}'.format(source_id))
            images = []
            if with_image:
                images = self.db.fetch_sql_all('SELECT * FROM image WHERE source_id={}'.format(source_id))

            return {
                'source': res,
                'image_list': images
            }

    def delete_source(self, source_id):
        sql = "DELETE FROM source WHERE source_id={}".format(source_id)
        self.db.exec_sql(sql, True)

        sql = "DELETE FROM image WHERE source_id={}".format(source_id)
        self.db.exec_sql(sql, True)

        ret = self.db.fetch_sql_all('SELECT * FROM source')

        self.db.close()
        return ret

    def save_annotation(self, data):
        alist = []
        try:
            alist = json.loads(data)
        except:
            print ('json syntax error')

        #print (alist)
        for d in alist:
            r = {}
            image_id = ''
            status = ''
            for x in d:
                if x == 'image_id':
                    image_id = d[x]
                elif x == 'status':
                    status = d[x]
                elif d[x] != '':
                    r[x] = d[x]

            #image_id = d['image_id']
            #del d['image_id']
            #print (image_id, d)
            if len(r):
                sql = "UPDATE image SET annotation='{}', status='{}', changed={} WHERE image_id='{}'".format(json.dumps(d), status, int(time.time()), image_id)
                self.db.exec_sql(sql)

        self.db.commit()
        self.db.close()


    def load_images(self):
        #sql = "SELECT *；；； FROM images WHERE key='{}'".format(args.key)
        #c.execute(sql)
        #print (c.fetchone())
        pass

    def _insert_db(self, path, image_list):
        ts_now = int(time.time())
        dir_name = os.path.split(path)[-1]

        sql = "INSERT INTO source (source_type, path, name, count, created) VALUES('folder', '{}', '{}', {}, {})".format(path, dir_name, len(image_list), ts_now)
        rid = self.db.exec_sql(sql, True)

        timestamp = None
        for i in image_list:
            exif  = i['img'].exif
            dtime = exif.get('DateTimeOriginal', '')
            via = 'exif'
            if dtime:
                dt = datetime.strptime(exif.get('DateTime', ''), '%Y:%m:%d %H:%M:%S')
                timestamp = dt.timestamp()
            else:
                stat = i['img'].get_stat()
                timestamp = int(stat.st_mtime)
                via = 'mtime'

            sql = "INSERT INTO image (path, name, timestamp, timestamp_via, status, annotation, changed, exif, source_id) VALUES ('{}','{}', {}, '{}', 'I','{}', {}, '{}', {})".format(
                i['path'],
                i['name'],
                timestamp,
                via,
                '',
                ts_now,
                json.dumps(exif),
                rid)

            self.db.exec_sql(sql)
        self.db.commit()

    def from_folder(self, path):
        #thumpy = Thumpy(thumb_dir, dir_path, is_debug)
        exist = self.db.fetch_sql("SELECT * FROM source WHERE path='{}'".format(path))
        if exist:
            print ('path added', exist)
            return []

        with os.scandir(path) as it:
            image_list = []
            for entry in it:
                if not entry.name.startswith('.') and \
                   entry.is_file() and \
                   _check_image_filename(entry):
                    img = ClamImage(entry.path)
                    image_list.append({
                        'path': entry.path,
                        'name': entry.name,
                        'img': img,
                    })

            # insert into database
            if self.db:
                self._insert_db(path, image_list)

            ret = self.db.fetch_sql_all('SELECT * FROM source')
            self.db.close()
            return ret

