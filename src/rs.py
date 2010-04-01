#!/usr/bin/python
# -*- coding: utf-8 -*-

MD5_READ_BLOCK_SIZE = 1048576
CSV_LOAD_DISPLAY_RATE = 10000
CHECK_PROGRESS_DIVIDER = 300.0

import sys
import os
import shutil
import csv
import hashlib
import locale

from const import *
from common import *
from pbar import ProgressBar
from cmd import OptionParser, OptionFormatter, OptionError

class Config(object):
    def __init__(self):
        self.encoding = locale.getpreferredencoding()
        self.source = None
        self.dest = None

config = Config()

class FatalError(Exception):
    def __init__(self, msg):
        self.msg = msg

def error(message):
    message = u'{0}: {1}'.format(APP_SHORT_NAME, message)
    print(message)
    return 1

def md5hash(path):
    ''' Считает md5-хеш файла и возвращает его строковое представление в нижнем регистра '''
    try:
        with open(path, 'rb') as fobject:
            hobj = hashlib.md5()
            block = fobject.read(MD5_READ_BLOCK_SIZE)
            while nonempty(block):
                hobj.update(block)
                block = fobject.read(MD5_READ_BLOCK_SIZE)
    except IOError as e:
        raise FatalError(u'ошибка при чтении файла {0}: {1!s}'.format(path, e))
    return hobj.hexdigest().lower()

def loadlibgen(csvname):
    ''' Загружает в память csv-файл с базой Library Genesis и возвращает словарь,
    где ключ — md5-хеш файла (строка в нижнем регистре), а значение — кортеж (путь к файлу, размер файла) '''

    try:
        with open(csvname) as csvfile:
            # инициализируем прогрессбар
            pbar = ProgressBar(maxval=len(open(csvname).readlines()))
            csvfile.seek(0)

            data = csv.reader(csvfile, delimiter=',', quotechar='"')
            # определяем, есть ли в файле заголовок
            # формат csv: путь, размер, md5
            try:
                # пытаемся преобразовать размер к целому числа
                int(second(data.next()))
            except ValueError:
                # нашли заголовок, стоим уже на второй строке
                pass
            else:
                # заголовка нет, идём обратно
                csvfile.seek(0)

            print(u'Загружаем в память базу Library Genesis...')

            # заполняем словарь
            library = {}
            values = ((os.path.normpath(first(entry)), int(second(entry)), third(entry)) for entry in data)
            for name, size, md5 in values:
                library[md5.lower()] = (name, size)

                # если выводить прогресс на каждом шаге, получается очень медленно
                # поэтому будем обновляться каждый CSV_LOAD_DISPLAY_RATE'ый шаг
                if data.line_num % CSV_LOAD_DISPLAY_RATE == 0:
                    pbar.set(data.line_num)
            
            pbar.finish()
    except Exception as e:
        raise FatalError(u'не удалось загрузить CSV-файл: {0!s}'.format(e))

    return library

def main(argv):
 
    # инициализируем парсер опций командной строки
    parser_usage = u'%prog [опции] <источник> <приёмник>'
    parser = OptionParser(parser_usage, version=APP_VERSION_STRING, prog=APP_SHORT_NAME,
        formatter=OptionFormatter(APP_VERSION, APP_LONG_NAME), add_help_option=False)
    parser.disable_interspersed_args()

    def usage():
        # временное решение (пока нету gettext)
        print(parser.format_help()[:-1].replace('Options', u'Опции'))
        return 0
    
    parser.add_option('-h', '--help', action='store_true', dest='help', default=False, 
        help=u'показать это сообщение и выйти')
    parser.add_option('-c', '--csv', dest='filename', default='libgen.csv', help=u'путь к CSV-файлу')
    parser.add_option('-m', '--method', dest='method', default='copy', 
        help=u'метод обработки файлов')
    parser.add_option('-r', '--remove-empty', action='store_true', dest='remove_empty', default=False,
        help=u'удалять пустые обработанные каталоги')
    #parser.add_option('-m', '--move', action='store_true', dest='move', default=False, 
    #    help=u'не копировать, а перемещать файлы')

    try:
        (options, args) = parser.parse_args()
    except OptionError as e:
        return error(e.msg)


    if empty(args) or options.help:
        return usage()
    if len(args) != 2:
        return error(u'количество аргументов не равно двум (источник и приёмник)')

    # источник и приёмник
    config.source = os.path.abspath(first(args)).decode(config.encoding)
    config.dest = os.path.abspath(second(args)).decode(config.encoding)

    # проверяем, все ли пути существуют
    if not os.path.isfile(options.filename):
        return error(u'CSV-файл {0} не найден'.format(options.filename))
    if not os.path.isdir(config.source):
        return error(u'директория {0} не найдена'.format(config.source))
    if not os.path.isdir(config.dest):
        return error(u'директория {0} не найдена'.format(config.dest))

    if not os.access(config.source, os.R_OK):
        return error(u'недостаточно прав для чтения из ' + config.source)
    if (options.move or options.remove_empty) and not os.access(config.source, os.W_OK):
        return error(u'недостаточно прав для записи в ' + config.source)
    if not os.access(config.dest, os.W_OK):
        return error(u'недостаточно прав для записи в ' + config.dest)

    try:
        # загружаем базу
        library = loadlibgen(options.filename) # library[md5] == (filename, size)
        libsizes = set(second(value) for value in library.values())

        print(u'Оцениваем общий размер анализируемых файлов...')
        source_size = dirsize(config.source)
        print(bytes_to_human(source_size))

        def process(source, dest):
            try:
                source = os.path.join(config.source, source)
                dest = os.path.join(config.dest, dest)
                if not os.path.isdir(os.path.dirname(dest)):
                    os.makedirs(os.path.dirname(dest))
                duplicate = os.path.isfile(dest)
                if options.move:
                    shutil.move(source, dest)
                else:    
                    shutil.copyfile(source, dest)
            except IOError:
                raise FatalError(u'ошибка при обработке файла {0}: {1!s}'.format(source, e))
            return duplicate
        
        def remove_if_empty(path):
            if options.remove_empty and dirsize(path) == 0:
                shutil.rmtree(path)
        
        print(u'Обрабатываем...')

        class ProgressCounter(object):
            def __init__(self):
                self.count, self.size = 0, 0
        
        processed, added, duplicate = ProgressCounter(), ProgressCounter(), ProgressCounter()

        # инициализируем индикатор прогресса
        pbar = ProgressBar(maxval=source_size, displaysize=True)
        delta = source_size / CHECK_PROGRESS_DIVIDER

        for path, dirs, files in os.walk(config.source):
            for file in files:
                fullpath = os.path.join(path, file)
                filesize = os.path.getsize(fullpath)
        
                # если в базе есть файл такого размера
                if filesize in libsizes:
                    md5 = md5hash(fullpath)
                    # и совпал по хешу
                    if md5 in library:
                        # то обрабатываем его
                        isduplicate = process(fullpath, first(library[md5]))
                        if isduplicate:
                            duplicate.count += 1
                            duplicate.size += filesize
                        else:
                            added.count += 1
                            added.size += filesize
                
                processed.count += 1
                processed.size += filesize
                
                # будем обновлять, только если накопилось достаточно файлов
                if processed.size - pbar.curval >= delta:
                    pbar.set(processed.size)

            remove_if_empty(path)

        remove_if_empty(config.source)
        pbar.finish()

    except FatalError as e:
        return error(e.msg)

    print(u'Обработано: {0} ({1})'.format(processed.count, bytes_to_human(processed.size)))
    print(u'Обнаружено дублей при добавлении: {0} ({1})'.format(duplicate.count, bytes_to_human(duplicate.size)))
    print(u'Добавлено в репозиторий: {0} ({1})'.format(added.count, bytes_to_human(added.size)))

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
