# -*- coding: utf-8 -*-

import os

def first(seq):
    return seq[0] if seq else None

def second(seq):
    return seq[1] if seq and len(seq) >= 2 else None

def third(seq):
    return seq[2] if seq and len(seq) >= 3 else None

def last(seq):
    return seq[-1] if seq and nonempty(seq) else None

def empty(seq):
    return len(seq) == 0

def nonempty(seq):
    return len(seq) != 0

def dirsize(path):
    size = 0
    for path, dirs, files in os.walk(path):
        size += sum(os.path.getsize(os.path.join(path, file)) for file in files)
    return size

def bytes_to_human(bytes):
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
            