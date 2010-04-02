# -*- coding: utf-8 -*-

from version import APP_VERSION

# информация о приложении
APP_AUTHOR = 'Roman Kharitonov'
APP_AUTHOR_MAIL = 'refaim.vl@gmail.com'
APP_URL = 'http://github.com/refaim/reposeer'

APP_LONG_NAME = 'Reposeer'
APP_SHORT_NAME = 'rs'

APP_VERSION_STRING = '{0} {1}\nby {2} ({3})'.format(
    APP_LONG_NAME, APP_VERSION, APP_AUTHOR, APP_AUTHOR_MAIL)

# константы основного модуля
MD5_READ_BLOCK_SIZE = 1048576
CSV_LOAD_DISPLAY_RATE = 10000
CHECK_PROGRESS_DIVIDER = 300.0

# методы обработки файлов
M_COPY = 'copy'
M_MOVE = 'move'
M_SYMLINK = 'symlink'
M_HARDLINK = 'hardlink'

# файловые системы
FS_NTFS = 'NTFS'