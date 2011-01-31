# -*- coding: utf-8 -*-
# author: Roman Kharitonov, refaim.vl@gmail.com

import sys

import console
from common import copy_args, bytes_to_human


class ProgressBar(object):
    @copy_args
    def __init__(self, maxval, fout=sys.stderr, width=None, displaysize=False, enabled=True):
        self.curval = 0
        self.terminal_width = console.getTerminalWidth()
        if self.width is None:
            # '[===...===] X%\n'
            # length of _getbarstr()
            self.width = self.terminal_width - len('[]') - len(' 100%\n')
            if self.displaysize:
                # subtract max length of size string
                self.width -= len(' [1023.99 GiB / 9999.99 TiB]')

    def update(self, value):
        assert value <= self.maxval
        assert (self.curval + value) <= self.maxval
        self.curval += value
        self._write()

    def set(self, value):
        assert value <= self.maxval
        self.curval = value
        self._write()

    def start(self):
        self.set(0)

    def finish(self):
        if self.curval != self.maxval:
            self.set(self.maxval)

    def _getbarstr(self):
        result = u'=' * int(self.percentage() * (self.width / 100.0))
        if self.curval != self.maxval:
            result += u'>'
        return result.ljust(self.width)

    def _getsizestr(self):
        fmt = u'[{cur} / {max}]'
        return fmt.format(
            cur = bytes_to_human(self.curval),
            max = bytes_to_human(self.maxval))

    def _write(self):
        if not self.enabled:
            return
        line = u'[{bar}] {prc}%'.format(
            bar = self._getbarstr(),
            prc = self.percentage()
            )
        if self.displaysize:
            line = u'{main} {size}'.format(
                main = line,
                size = self._getsizestr()
                )

        if self.curval == self.maxval:
            ending = u'\n'
        else:
            ending = u'\r'
        line = line.ljust(self.terminal_width - len(ending)) + ending

        # encoding is None if output redirected to a file
        if self.fout.encoding:
            line = line.encode(self.fout.encoding)

        self.fout.write(line)
        self.fout.flush()

    def percentage(self):
        return int(self.curval / float(self.maxval) * 100.0)

    def clear(self):
        '(Temporarily) clear progress bar off screen, e.g. to write log line.'
        if not self.enabled:
            return
        self.fout.write(' ' * (self.terminal_width - len('\r')) + '\r')
        self.fout.flush()


class ProgressBarSafeLogger(object):
    'Wraps logger to clear progress bar before logging something.'
    @copy_args
    def __init__(self, log, pbar=None):
        pass

    def set_pbar(self, pbar):
        self.pbar = pbar

    def unset_pbar(self):
        self.pbar = None

    def debug(self, *args, **kw):
        self.pbar.clear()
        self.log.debug(*args, **kw)

    def info(self, *args, **kw):
        self.pbar.clear()
        self.log.info(*args, **kw)

    def warning(self, *args, **kw):
        self.pbar.clear()
        self.warning.info(*args, **kw)

    def error(self, *args, **kw):
        self.pbar.clear()
        self.error.info(*args, **kw)
