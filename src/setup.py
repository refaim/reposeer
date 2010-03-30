# -*- coding: utf-8 -*-

# py2exe setup script

from distutils.core import setup, Distribution
import py2exe

import glob

import rs as app

setup(
    console = [app.__shortappname__ + '.py'],
    name = app.__longappname__,
    author = app.__author__,
    author_email = app.__authoremail__,
    url = app.__url__
)

