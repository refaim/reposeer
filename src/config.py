# -*- coding: utf-8 -*-

import sys
import shutil
import locale

from const import *
from common import *

class Config(object):
    ''' Класс, содержащий различные параметры, нужные для работы '''
    def __init__(self):
        self.encoding = locale.getpreferredencoding()
        self.source = None
        self.dest = None
        self.method = None

        self.windows = False
        self.unix = False
        self.symlink_allowed = False
        self.setmethods()

    def setmethods(self):
        ''' Инициализация методов обработки файлов '''

        # пытаемся обнаружить функции создания жёстких и мягких ссылок
        try:
            # в UNIX всё просто
            from os import link as hardlink, symlink
            self.unix = True
        except ImportError:
            # а в Windows уже сложнее
            if sys.platform == 'win32':

                import pywintypes
                self.windows = True
                
                # получили версию Windows
                winver = float('{0[0]}.{0[1]}'.format(sys.getwindowsversion()))

                WINDOWS_2000 = 5.0
                WINDOWS_VISTA = 6.0

                if winver >= WINDOWS_2000:
                    from win32file import CreateHardLink

                    def hardlink(src, dest):
                        try:
                            CreateHardLink(dest, src)
                        except pywintypes.error as e:
                            raise FatalError(errmsg.format(e[2]))
                            
                else:
                    hardlink = None

                if winver >= WINDOWS_VISTA:
                    from win32file import CreateSymbolicLink

                    def symlink(src, dest):
                        try:
                            CreateSymbolicLink(dest, src)
                        except pywintypes.error as e:
                            raise FatalError(errmsg.format(e[2]))

                    # теперь проверим, хватает ли нам привилегий
                    # не стал ковыряться в WinAPI, нашёл готовый модуль
                    from check_symlink import enable_symlink_privilege

                    assigned = enable_symlink_privilege()
                    if assigned:
                        self.symlink_allowed = True
                    else:
                        symlink = None
                        self.symlink_allowed = False

                else:
                    symlink = None

            else:
                # ничего не нашли, работаем непонятно где
                hardlink = symlink = None

        self.methods = {
            M_COPY: shutil.copyfile,
            M_MOVE: shutil.move,
            M_HARDLINK: hardlink,
            M_SYMLINK: symlink }

        suffix = u'не поддерживает создание {0} ссылок на файлы'
        if self.windows:
            prefix = u'Ваша версия Windows'
        else:
            prefix = u'Ваша операционная система'

        symlink_str = u'мягких (символических)'
        hardlink_str = u'жёстких'

        self.method_errors = {
            M_SYMLINK: u'{0} {1}'.format(prefix, suffix.format(symlink_str)),
            M_HARDLINK: u'{0} {1}'.format(prefix, suffix.format(hardlink_str))
        }

        if not self.symlink_allowed:
            self.method_errors[M_SYMLINK] =\
                u'Недостаточно привилегий для создания {0} ссылок'.format(symlink_str)

        self.method_descriptions = {
            M_COPY: u'скопировано',
            M_MOVE: u'перемещено',
            M_SYMLINK: u'созданы мягкие ссылки',
            M_HARDLINK: u'созданы жёсткие ссылки'
        }

