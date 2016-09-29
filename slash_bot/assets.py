# coding: utf-8

"""
Created on 2016-09-28
@author: naoey
"""

import os

import config

from PIL import Image
from errors import *

class AssetStore(object):
    @staticmethod
    def get(name):
        location = os.path.join(config.PATHS["assets"], "{}.png".format(name))
        try:
            return Image.open(location)
        except IOError:
            raise AssetsError("Couldn't find file for {}".format(location))

    @staticmethod
    def store(image, name):
        location = os.path.join(config.PATHS["assets"], "{}.png".format(name))
        try:
            dirname, fname = os.path.split(location)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            image.save(location)
        except IOError:
            raise AssetsError("Couldn't store asset at {}".format(location))