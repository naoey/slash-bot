# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import sys
import linecache
import random
import string


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return "EXCEPTION IN ({}, LINE {} \"{}\"): {}".format(filename, lineno, line.strip(), exc_obj)


def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider


def random_string(size=6):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))
