# -*- coding: utf-8 -*-

import os
import inspect
import functools


class ReposeerException(Exception): pass

def copy_args(func):
    '''
        Decorator.
        Initializes object attributes by the initializer signature.
        Usage:

        class foo(bar):
            @copy_args
            def __init__(self, arg1, arg2): pass

        foobar = foo(1, 2)
        foobar.arg1 == 1 and foobar.arg2 == 2 # True
    '''
    argspec = inspect.getargspec(func)
    argnames = argspec.args[1:]
    if argspec.defaults:
        defaults = dict(zip(argnames[-len(argspec.defaults):], argspec.defaults))
    else:
        defaults = {}

    @functools.wraps(func)
    def __init__(self, *args, **kwargs):
        args_it = iter(args)
        for key in argnames:
            if key in kwargs:
                value = kwargs[key]
            else:
                try:
                    value = next(args_it)
                except StopIteration:
                    value = defaults[key]
            setattr(self, key, value)
        func(self, *args, **kwargs)
    return __init__

def dirsize(path):
    size = 0
    for path, dirs, files in os.walk(path):
        size += sum(os.path.getsize(os.path.join(path, file)) for file in files)
    return size

def bytes_to_human(bytes):
    bounds = {
        1024 ** 4: 'TiB',
        1024 ** 3: 'GiB',
        1024 ** 2: 'MiB',
        1024:      'KiB',
        0:         'bytes'
    }

    bytes = float(bytes)
    for bound in sorted(bounds.keys(), reverse=True):
        if bytes >= bound:
            if bound != 0:
                bytes = bytes / bound
            return '{0:.2f} {1}'.format(bytes, bounds[bound])
