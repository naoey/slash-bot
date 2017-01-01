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
from .player import STATE, MusicPlayer

logger = logging.getLogger(__name__)

BOT = config.GLOBAL["bot"]

_players = {}


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

        @overrides(Command)
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

    class QueueSong(Command):
        command = "queue"
        aliases = ["q", "add"]
        required_permissions = [PERMISSIONS.SERVER_ADMIN, ]
        silent_permissions = True

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        def _get_server_default_vc(self):
            try:
                return MusicConfiguration.get(server=self._raw_message.server.id).default_channel
            except MusicConfiguration.DoesNotExist as e:
                return None

        @overrides(Command)
        async def make_response(self):
            if BOT.is_voice_connected(self._raw_message.server):
                self.response = "Already connected to a voice channel!"
                return

            vc = None
            self.response = "Hue"
            if vc is None:
                if self.invoker.voice.voice_channel is None:
                    logger.debug("Can't queue song because invoker isn't in a voice channel and server doesn't have a default")
                    raise NoVoiceChannelError(
                        "You need to be in a voice channel or the server should have a default channel",
                        mention=self.invoker.mention
                    )
                else:
                    vc = self.invoker.voice.voice_channel
                    logger.debug("Voice channel for invoker is {}".format(self.invoker.voice.voice_channel))

            voice_conn = await BOT.join_voice_channel(vc)
            logger.debug("Bot voice status is {}".format(BOT.is_voice_connected(self._raw_message.server)))

            player = await voice_conn.create_ytdl_player("https://www.youtube.com/watch?v=eeQ5Nd3I3YI&app=desktop")
            player.start()
