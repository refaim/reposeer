# -*- coding: utf-8 -*-

import csv
import MySQLdb

from pbar import ProgressBar
from common import copy_args

PROGRESSBAR_UPDATE_INTERVAL = 10000

class CSVLoader(object):
    @copy_args
    def __init__(self, filename):
        self.fieldnames = ('filename', 'filesize', 'md5')

    def load(self):
        fobj = open(self.filename)
        pbar = ProgressBar(maxval=len(fobj.readlines()))
        fobj.seek(0)
        reader = csv.DictReader(fobj, fieldnames=self.fieldnames)

        # skip header
        header = reader.next()
        for fieldname in header:
            if fieldname != header[fieldname].lower():
                # header not found
                fobj.seek(0)
                break

        library = {}
        for entry in reader:
            library[entry['md5'].lower()] = (entry['filename'], int(entry['filesize']))
            if reader.line_num % PROGRESSBAR_UPDATE_INTERVAL == 0:
                pbar.set(reader.line_num)
        pbar.finish()
        fobj.close()
        return library

class DBLoader(object):
    @copy_args
    def __init__(self, host, name, user, passwd):
        pass

    def load(self):
        conn = MySQLdb.connect(host=self.host, db=self.name, user=self.user, passwd=self.passwd, use_unicode=True)
        cursor = conn.cursor()
        cursor.execute("SELECT Filename, Filesize, MD5 FROM updated WHERE Filename != ''")
        library = {}
        for entry in cursor:
            name, size, md5 = entry
            library[md5.lower()] = (name, size)
        cursor.close()
        conn.close()
        return library
