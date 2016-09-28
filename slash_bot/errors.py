# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

class SlashBotError(Exception):
    pass

class ConfigError(SlashBotError):
    def __init__(self, config_attr=None):
        if config_attr:
            super().init("Missing/invalid config for {}".format(config_attr))
        else:
            super().init()

class SlashBotValueError(SlashBotError):
    pass

class CommandFormatError(SlashBotError):
    pass

class ThirdPartyAPIError(SlashBotError):
    pass

class AssetsError(SlashBotError):
    pass