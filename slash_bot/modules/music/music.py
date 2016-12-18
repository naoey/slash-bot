# coding: utf-8

"""
Created on 2016-11-22
@author: naoey
"""

import logging
import datetime

from discord import ChannelType

import config

from errors import *
from models import *
from commands import *
from utils import *

logger = logging.getLogger(__name__)

BOT = config.GLOBAL["bot"]


class Music(Command):
    command = "music"
    aliases = ["m", ]

    def __init__(self, message):
        super().__init__(message)

        self.subcommands_map = {}
        for cmd in MusicFunctions.__dict__.values():
            if isinstance(cmd, type) and issubclass(cmd, Command):
                if len(cmd.command) > 0:
                    self.subcommands_map[cmd.command] = cmd
                    if len(cmd.aliases) > 0:
                        for each in cmd.aliases:
                            self.subcommands_map[each] = cmd

    def get_delegate_command(self):
        if len(self.params) > 0 and self.params[0] in self.subcommands_map.keys():
            return self.subcommands_map[self.params[0]](self._raw_message)

    @classmethod
    async def create_command(cls, message):
        return Music(message).get_delegate_command()


class MusicFunctions(object):
    class SetDefaultChannel(Command):
        command = "setchannel"
        aliases = ["setch", ]
        required_permissions = [PERMISSIONS.SERVER_ADMIN, ]
        silent_permissions = True

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        async def make_response(self):
            await super().make_response()

            try:
                channel = [channel for channel in self._raw_message.server.channels
                           if string_compare(channel.name, self.params[0]) and
                           channel.type == ChannelType.voice][0]
                logger.debug("Got channel {}".format(channel))

                new_configuration = {
                    "default_channel": channel.id,
                    "last_modified": datetime.datetime.now(),
                }

                music_configuration, created = MusicConfiguration.get_or_create(
                    server=channel.server.id,
                    defaults=new_configuration
                )

                if not created:
                    r = MusicConfiguration.update(**new_configuration).where(
                        MusicConfiguration.server == self._raw_message.server.id
                    ).execute()

                    if r == 1:
                        self.response = "Updated default music channel to {channel_name} 👍".format(
                            channel_name=channel.name
                        )
                    else:
                        raise SlashBotError("An error occurred while updating the default music channel!")
            except IndexError:
                raise SlashBotValueError("Couldn't find the channel you mentioned!", mention=self.invoker.mention)
