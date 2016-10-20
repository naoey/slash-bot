# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""


class SlashBotError(Exception):
    def __init__(self, message, mention=None):
        super().__init__(message)
        self.to_be_mentioned = mention


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


class CommandDefinitionError(SlashBotError):
    pass


class SlashBotPermissionError(SlashBotError):
    def __init__(self, message, mention=None, silent=False):
        super().__init__(message, mention)
        self.silent = silent


class BotPermissionError(SlashBotPermissionError):
    pass


class DiscordPermissionError(SlashBotPermissionError):
    pass
