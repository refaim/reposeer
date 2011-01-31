# -*- coding: utf-8 -*-

import sys
import shutil
import locale
import traceback

import console
from common import ReposeerException

# file processing methods
M_COPY = 'copy'
M_MOVE = 'move'
M_SYMLINK = 'symlink'
M_HARDLINK = 'hardlink'

# file systems
FS_NTFS = 'NTFS'

class Config(object):
    def __init__(self):
        self.terminal_width = console.getTerminalWidth()
        self.encoding = locale.getpreferredencoding()

        self.methods = {
            M_COPY: shutil.copyfile,
            M_MOVE: shutil.move,
            M_HARDLINK: None,
            M_SYMLINK: None,
        }
        self.link_method_names = {
            M_HARDLINK: 'hard',
            M_SYMLINK: 'symbolic',
        }
        self.method_descriptions = {
            M_COPY: 'copied',
            M_MOVE: 'moved',
            M_HARDLINK: 'created hard links',
            M_SYMLINK: 'created symbolic links',
        }
        self.symlink_allowed = True

        if 'win32' in sys.platform:
            self.windows = True
            self._process_windows()
        else:
            self.windows = False
            try:
                # UNIX
                from os import link as hardlink, symlink
                self.methods[M_HARDLINK] = hardlink
                self.methods[M_SYMLINK] = symlink
            except ImportError:
                # unknown platform
                pass

    def _process_windows(self):
        import pywintypes
        errmsg = u"Error while processing '{0}': {1!s}"

        winver = float('{0[0]}.{0[1]}'.format(sys.getwindowsversion()))
        WINDOWS_2000 = 5.0
        WINDOWS_VISTA = 6.0

        if winver >= WINDOWS_2000:
            from win32file import CreateHardLink
            def hardlink(src, dst):
                try:
                    CreateHardLink(dst, src)
                except pywintypes.error, e:
                    raise ReposeerException(errmsg.format(src, e[2]))
            self.methods[M_HARDLINK] = hardlink

        if winver >= WINDOWS_VISTA:
            from win32file import CreateSymbolicLink
            from check_symlink import enable_symlink_privilege

            if enable_symlink_privilege():
                def symlink(src, dst):
                    try:
                        CreateSymbolicLink(dst, src)
                    except pywintypes.error, e:
                        raise ReposeerException(errmsg.format(src, e[2]))
                self.methods[M_SYMLINK] = symlink
            else:
                self.symlink_allowed = False

    def get_error_message(self, method):
        unsupported = 'Your operating system does not support {0} links'
        if method == M_SYMLINK and not self.symlink_allowed:
            return 'Not enough rights to create symbolic links'
        else:
            return unsupported.format(self.link_method_names[method])

    def checkfs(self, method):
        from win32api import GetVolumeInformation
        from win32file import GetVolumePathName

        src_volume = GetVolumePathName(self.src)
        dst_volume = GetVolumePathName(self.dst)
        if method == M_HARDLINK and src_volume != dst_volume:
            return 'Hard links can be created only within a single logical drive'

        errmsg = 'File system on drive {0} does not support {0} links'
        src_fs = GetVolumeInformation(src_volume)[-1]
        dst_fs = GetVolumeInformation(dst_volume)[-1]
        if src_fs != FS_NTFS:
            return errmsg.format(src_volume, self.link_method_names[method])
        if dst_fs != FS_NTFS:
            return errmsg.format(dst_volume, self.link_method_names[method])
        return None
