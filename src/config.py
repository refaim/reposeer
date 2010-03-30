# -*- coding: utf-8 -*-

import locale

class Config(object):
    def __init__(self):
        
        if locale.getlocale() != (None, None):
            locale.setlocale(locale.LC_ALL, '')
        self.encoding = locale.getpreferredencoding()

        self.source = None
        self.dest = None
