# -*- coding: utf-8 -*-
# author: Roman Kharitonov, refaim.vl@gmail.com

import sys

class ProgressBar(object):
    def __init__(self, maxval, fout=sys.stderr, width=50, displaysize=False):
        self.curval, self.maxval = 0, maxval
        self.fout = fout
        self.width = width
        self.displaysize = displaysize

    def update(self, value):
        assert value <= self.maxval 
        assert self.curval + value <= self.maxval
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
        return (u'=' * int(self.percentage() * (self.width / 100.0))
                + u'>').ljust(self.width)

    def _getsizestr(self):
        fmt = u'[{cur} / {max}]'
        return fmt.format(
            cur = convert_bytes(self.curval),
            max = convert_bytes(self.maxval))

    def _write(self):
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
            suffix = u'\n'
        else:
            suffix = u'\r'

        self.fout.write((line.ljust(max(len(line), 79)) + suffix).encode(self.fout.encoding))
        self.fout.flush()

    def percentage(self):
        return int(self.curval / float(self.maxval) * 100.0)

def convert_bytes(bytes):
    bounds = { 1024 ** 5: u'Пбайт',
               1024 ** 4: u'Тбайт',
               1024 ** 3: u'Гбайт',
               1024 ** 2: u'Мбайт',
               1024:      u'Кбайт',
               0:         u'байт' }

    bytes = float(bytes)
    for bound in sorted(bounds.keys(), reverse=True):
        if bytes >= bound:
            if bound != 0:
                bytes = bytes / bound
            return u'{0:.2f} {1}'.format(bytes, bounds[bound])
