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
            