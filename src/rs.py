#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import hashlib
import shutil
import optparse
import traceback

import loader
from version import APP_VERSION
from common import ReposeerException, dirsize, bytes_to_human
from pbar import ProgressBar
from config import *


APP_AUTHOR = 'Roman Kharitonov'
APP_AUTHOR_MAIL = 'refaim.vl@gmail.com'
APP_URL = 'http://github.com/refaim/reposeer'

APP_LONG_NAME = 'Reposeer'
APP_SHORT_NAME = 'rs'

APP_VERSION_STRING = '{0} {1} by {2} ({3})'.format(
    APP_LONG_NAME, APP_VERSION, APP_AUTHOR, APP_AUTHOR_MAIL)

CHECK_PROGRESS_DIVIDER = 300.0
MD5_READ_BLOCK_SIZE = 2 ** 20 # one mbyte


class ProgressCounter(object):
    def __init__(self):
        self.count, self.size = 0, 0

    def add(self, size):
        self.count += 1
        self.size += size

def error(message):
    print(u'{0}: {1}'.format(APP_SHORT_NAME, message))
    return 1

def process(src, dst, options):
    errmsg = u'Error while processing file {0}'.format(src) + u':\n{0!s}'
    try:
        src = os.path.normpath(os.path.join(config.src, src))
        dst = os.path.normpath(os.path.join(config.dst, dst))
        duplicate = os.path.isfile(dst)
        if options.dry_run:
            return duplicate
        if not os.path.isdir(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        try:
            if not duplicate:
                config.methods[options.method](src, dst)
            elif options.remove_duplicates:
                os.remove(src)
        except OSError, ex:
            raise ReposeerException(errmsg.format(traceback.format_exc()))
    except IOError, ex:
        raise ReposeerException(errmsg.format(traceback.format_exc()))
    return duplicate

def md5hash(path):
    ''' Считает md5-хеш файла и возвращает его строковое представление в нижнем регистре '''
    with open(path, 'rb') as fobj:
        hobj = hashlib.md5()
        block = fobj.read(MD5_READ_BLOCK_SIZE)
        while block:
            hobj.update(block)
            block = fobj.read(MD5_READ_BLOCK_SIZE)
    return hobj.hexdigest().lower()

def main():
    global config
    oparser = optparse.OptionParser(
        usage='%prog [options] <source> <destination>',
        version=APP_VERSION_STRING,
        prog=APP_SHORT_NAME)
    oparser.disable_interspersed_args()

    oparser.add_option('-n', '--dry-run', action='store_true', dest='dry_run', default=False,
        help="don't perform write actions, just simulate")

    optgroup = optparse.OptionGroup(oparser, 'File handling options')
    optgroup.add_option('-m', '--method', dest='method', default=M_COPY,
        help='file processing method ({0})'.format('|'.join(config.methods)))
    optgroup.add_option('-r', '--remove-empty', action='store_true',
        dest='remove_empty', default=False, help='remove empty directories')
    optgroup.add_option('', '--remove-duplicates', action='store_true',
        dest='remove_duplicates', default=False,
        help='remove files that already exist in repository')
    oparser.add_option_group(optgroup)

    optgroup = optparse.OptionGroup(oparser, 'CSV options')
    optgroup.add_option('', '--csv', dest='csv', metavar='FILENAME', default='libgen.csv',
        help='path to csv (%default)')
    oparser.add_option_group(optgroup)

    optgroup = optparse.OptionGroup(oparser, "DB connection options")
    optgroup.add_option('', '--db-host', default='localhost', help='DB host (%default)')
    optgroup.add_option('', '--db-name', default='bookwarrior', help='DB name (%default)')
    optgroup.add_option('', '--db-user', help='DB user')
    optgroup.add_option('', '--db-passwd', metavar='PASSWD', default='', help='DB password (empty)')
    oparser.add_option_group(optgroup)

    (options, args) = oparser.parse_args()
    if len(args) != 2:
        oparser.error('Wrong number of arguments')
    if options.method not in config.methods:
        oparser.error(u'Unknown file processing method "{0}"'.format(options.method))
    if config.methods[options.method] is None:
        return error(config.get_error_message(options.method))

    config.src, config.dst = (os.path.abspath(arg).decode(config.encoding)
        for arg in args)

    if not os.path.isdir(config.src):
        return error(u'Directory {0} not found'.format(config.src))
    if not os.path.isdir(config.dst):
        return error(u'Directory {0} not found'.format(config.dst))

    if not os.access(config.src, os.R_OK):
        return error(u'Not enough rights for reading from %s' % config.src)
    if ((options.remove_empty or options.remove_duplicates or options.method == M_MOVE)
        and not os.access(config.src, os.W_OK)
    ):
        return error(u'Not enough rights for writing to %s' % config.src)
    if not os.access(config.dst, os.W_OK):
        return error(u'Not enough rights for writing to %s' % config.dst)

    # проверим, поддерживает ли файловая система создание ссылок
    # в Windows мягкие и жёсткие ссылки можно создавать только на NTFS
    # (жёсткие — только в пределах одного диска)
    if config.windows and options.method in (M_SYMLINK, M_HARDLINK):
        message = config.checkfs(options.method)
        if message:
            return error(message)

    if options.db_user:
        worker = loader.DBLoader(options.db_host, options.db_name, options.db_user, options.db_passwd)
    else:
        if not os.path.isfile(options.csv):
            return error(u'File {0} not found'.format(options.csv))
        worker = loader.CSVLoader(options.csv)

    print('Loading Library Genesis...')
    library = worker.load()
    library_filesizes = set(value[1] for value in library.values())
    print('{0} books loaded'.format(len(library)))

    print('Analyzing total size of files for processing...', end=' ')
    src_size = dirsize(config.src)
    print(bytes_to_human(src_size))
    print('Scanning...')

    processed, added, duplicate = ProgressCounter(), ProgressCounter(), ProgressCounter()
    pbar = ProgressBar(maxval=src_size, displaysize=True)
    delta = src_size / CHECK_PROGRESS_DIVIDER
    for path, dirs, files in os.walk(config.src):
        for file in files:
            fullpath = os.path.join(path, file)
            filesize = os.path.getsize(fullpath)

            # если в базе есть файл такого размера
            if filesize in library_filesizes:
                md5 = md5hash(fullpath)
                # и совпал по хешу
                if md5 in library:
                    # то обрабатываем его
                    already_in_repo = process(fullpath, library[md5][0], options)
                    if already_in_repo:
                        duplicate.add(filesize)
                    else:
                        added.add(filesize)

            processed.add(filesize)
            # будем обновлять, только если накопилось достаточно файлов
            if processed.size - pbar.curval >= delta:
                pbar.set(processed.size)
        if not options.dry_run and options.remove_empty and dirsize(path) == 0:
            shutil.rmtree(path)

    pbar.finish()

    print('Processed: {0} ({1})'.format(
        processed.count, bytes_to_human(processed.size)))
    print('Added to repository ({0}): {1} ({2})'.format(
        config.method_descriptions[options.method], added.count, bytes_to_human(added.size)))
    print('Duplicates {0}: {1} ({2})'.format(
        'removed' if options.remove_duplicates else 'found',
        duplicate.count, bytes_to_human(duplicate.size)))

    return 0

if __name__ == '__main__':
    try:
        config = Config()
        sys.exit(main())
    except KeyboardInterrupt:
        print('Interrupted by user'.ljust(config.terminal_width))
    except ReposeerException, ex:
        print(ex.args[0])
    sys.exit(1)
