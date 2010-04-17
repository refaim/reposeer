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
        self.symlink_allowed = True # будем считать, что можно
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
            if sys.platform != 'win32':
                # ничего не нашли, работаем непонятно где
                hardlink = symlink = None
            else:
                import pywintypes
                self.windows = True
                errmsg = u'Ошибка при обработке файла {0}: {1!s}'
                
                # получили версию Windows
                winver = float('{0[0]}.{0[1]}'.format(sys.getwindowsversion()))

                WINDOWS_2000 = 5.0
                WINDOWS_VISTA = 6.0

                if winver < WINDOWS_2000:
                    hardlink = None
                else:
                    from win32file import CreateHardLink

                    def hardlink(src, dest):
                        try:
                            CreateHardLink(dest, src)
                        except pywintypes.error as e:
                            raise FatalError(errmsg.format(src, e[2]))

                if winver < WINDOWS_VISTA:
                    symlink = None
                else:
                    from win32file import CreateSymbolicLink

                    def symlink(src, dest):
                        try:
                            CreateSymbolicLink(dest, src)
                        except pywintypes.error as e:
                            raise FatalError(errmsg.format(src, e[2]))

                    # теперь проверим, хватает ли нам привилегий
                    # не стал ковыряться в WinAPI, нашёл готовый модуль
                    from check_symlink import enable_symlink_privilege

                    assigned = enable_symlink_privilege()
                    if assigned:
                        self.symlink_allowed = True
                    else:
                        symlink = None
                        self.symlink_allowed = False

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

        self.method_str = {
            M_SYMLINK: u'мягких (символических)',
            M_HARDLINK: u'жёстких'
        }

        self.method_errors = {
            M_SYMLINK: u'{0} {1}'.format(prefix, suffix.format(self.method_str[M_SYMLINK])),
            M_HARDLINK: u'{0} {1}'.format(prefix, suffix.format(self.method_str[M_HARDLINK]))
        }

        if not self.symlink_allowed:
            self.method_errors[M_SYMLINK] =\
                u'Недостаточно привилегий для создания {0} ссылок'.format(self.method_str[M_SYMLINK])

        self.method_descriptions = {
            M_COPY: u'скопировано',
            M_MOVE: u'перемещено',
            M_SYMLINK: u'созданы мягкие ссылки',
            M_HARDLINK: u'созданы жёсткие ссылки'
        }

    def checkfs(self, filemethod):
        from win32api import GetVolumeInformation
        from win32file import GetVolumePathName
    
        source_volume = GetVolumePathName(self.source)
        dest_volume = GetVolumePathName(self.dest)
        if filemethod == M_HARDLINK and source_volume != dest_volume:
            raise FatalError(u'Нельзя создать на диске {0} жёсткую ссылку на файл с диска {1}'.format(
                dest_volume, source_volume))

        source_fs = last(GetVolumeInformation(source_volume))
        dest_fs = last(GetVolumeInformation(dest_volume))

        errmsg = u'Файловая система {0} на диске {1} не является NTFS и не поддерживает создание {2} ссылок'
        if source_fs != FS_NTFS:
            raise FatalError(errmsg.format(source_fs, source_volume, self.method_str[filemethod]))
        if dest_fs != FS_NTFS:
            raise FatalError(errmsg.format(dest_fs, dest_volume, self.method_str[filemethod]))
