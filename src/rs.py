#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Roman Kharitonov'
__authoremail__ = 'refaim.vl@gmail.com'
__url__ = 'http://github.com/refaim/reposeer'
__longappname__ = 'Reposeer'
__shortappname__ = 'rs'
__version__ = 0.5
__versionstring__ = '{0} {1}\nby {2} ({3})'.format(
    __longappname__, __version__, __author__, __authoremail__)

MD5_READ_BLOCK_SIZE = 1048576
CSV_LOAD_DISPLAY_RATE = 10000
CHECK_PROGRESS_DIVIDER = 300.0

import sys
import os
import shutil
import csv
import hashlib

from common import *
from config import Config
from pbar import ProgressBar, convert_bytes
from cmd import OptionParser, OptionFormatter, OptionError

config = Config()

class GError(Exception):
    def __init__(self, msg):
        self.msg = msg

def error(message, fname=None):
    message = u'{0}: {1}'.format(__shortappname__, message)
    if fname is not None:
        message += u': {0}'.format(fname)
    print(message)
    return 2

def md5hash(path):
    with open(path, 'rb') as fobject:
        hobj = hashlib.md5()
        block = fobject.read(MD5_READ_BLOCK_SIZE)
        while nonempty(block):
            hobj.update(block)
            block = fobject.read(MD5_READ_BLOCK_SIZE)
    return hobj.hexdigest().lower()

def loadlibgen(csvname):
    library = {}

    with open(csvname) as csvfile:
        pbar = ProgressBar(maxval=len(open(csvname).readlines()))
        csvfile.seek(0)
        data = csv.reader(csvfile, delimiter=',', quotechar='"')
        try:
            int(second(data.next()))
        except ValueError:
            pass
        else:
            csvfile.seek(0)

        print(u'Загружаем в память базу Library Genesis...')
        # (путь, размер, md5)
        values = ((os.path.normpath(first(entry)), int(second(entry)), third(entry)) for entry in data)
        try:
            for name, size, md5 in values:
                library[md5.lower()] = (name, size)
                if data.line_num % CSV_LOAD_DISPLAY_RATE == 0:
                    pbar.set(data.line_num)
            pbar.finish()
        except Exception as e:
            raise GError(u'ошибка при загрузке csv: {0!s}'.format(e))

    return library

def main(argv):
    parser_usage = u'%prog [опции] <источник> <приёмник>'
    parser = OptionParser(parser_usage, version=__versionstring__, prog=__shortappname__,
        formatter=OptionFormatter(__version__, __longappname__), add_help_option=False)
    parser.disable_interspersed_args()
    parser.add_option('-h', '--help', action='help', help=u'показать это сообщение и выйти')
    parser.add_option('-c', '--csv', dest='filename', default='libgen.csv', help=u'путь к CSV-файлу')
    parser.add_option('-m', '--move', action='store_true', dest='move', default=False, 
        help=u'не копировать, а перемещать файлы')
    parser.add_option('-r', '--remove-empty', action='store_true', dest='remove_empty', default=False,
        help=u'удалять пустые обработанные каталоги')

    try:
        (options, args) = parser.parse_args()
    except OptionError as e:
        return error(e.msg)

    if empty(args):
        print(parser.format_help()[:-1].replace('Options', u'Опции'))
        return 0
    if len(args) != 2:
        return error(u'неправильное число аргументов: {0} вместо двух'.format(len(args)))

    config.source = os.path.abspath(first(args)).decode(config.encoding)
    config.dest = os.path.abspath(second(args)).decode(config.encoding)

    if not os.path.isfile(options.filename):
        return error(u'не найден файл', options.filename)
    if not os.path.isdir(config.source):
        return error(u'не найдена директория', config.source)
    if not os.path.isdir(config.dest):
        return error(u'не найдена директория', config.dest)

    if not os.access(config.source, os.R_OK):
        return error(u'доступ на чтение запрещён', config.source)
    if (options.move or options.remove_empty) and not os.access(config.source, os.W_OK):
        return error(u'доступ на запись запрещён', config.source)
    if not os.access(config.dest, os.W_OK):
        return error(u'доступ на запись запрещён', config.dest)

    try:
        library = loadlibgen(options.filename) # library[md5] == (filename, size)
        libsz = set(second(value) for value in library.values())

        print(u'Оцениваем общий размер анализируемых файлов...')
        source_size = dirsize(config.source)
        print(convert_bytes(source_size))

        def process(source, dest):
            source = os.path.join(config.source, source)
            dest = os.path.join(config.dest, dest)
            if not os.path.isdir(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            duplicate = os.path.isfile(dest)
            if options.move:
                shutil.move(source, dest)
            else:    
                shutil.copyfile(source, dest)
            return duplicate

        print(u'Обрабатываем...')
        processed_count, processed_size = 0, 0
        added_count, added_size = 0, 0
        dup_count, dup_size = 0, 0

        pbar = ProgressBar(maxval=source_size, displaysize=True)
        processed_size = 0
        delta = source_size / CHECK_PROGRESS_DIVIDER
        for path, dirs, files in os.walk(config.source):
            for file in files:
                fullpath = os.path.join(path, file)
                fsize = os.path.getsize(fullpath)
                if fsize in libsz:
                    md5 = md5hash(fullpath)
                    if md5 in library:
                        isdup = process(fullpath, first(library[md5]))
                        if isdup:
                            dup_count += 1
                            dup_size += fsize
                        else:
                            added_count += 1
                            added_size += fsize
                processed_size += fsize
                if processed_size >= delta:
                    pbar.update(processed_size)
                    processed_size = 0
                processed_count += 1
            if options.remove_empty and dirsize(path) == 0:
                shutil.rmtree(path)
        if options.remove_empty and dirsize(config.source) == 0:
            shutil.rmtree(config.source)
        pbar.finish()

    except GError as e:
        return error(e.msg)

    print(u'Обработано: {0} ({1})'.format(processed_count, convert_bytes(source_size)))
    print(u'Обнаружено дублей при добавлении: {0} ({1})'.format(dup_count, convert_bytes(dup_size)))
    print(u'Добавлено в репозиторий: {0} ({1})'.format(added_count, convert_bytes(added_size)))

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
