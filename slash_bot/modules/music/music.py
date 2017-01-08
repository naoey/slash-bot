# coding: utf-8

"""
Created on 2016-11-22
@author: naoey
"""

import logging
import datetime
import urllib
from bs4 import BeautifulSoup

from discord import ChannelType

import config

from errors import *
from models import *
from commands import *
from utils import *
from .player import STATE, YoutubePlayer

logger = logging.getLogger(__name__)

BOT = config.GLOBAL["bot"]

_players = {}


class Music(Command):
    '''Base command for general music configuration etc.'''


class YoutubeMusic(Command):
    '''Base command for all music functions that play from YouTube.'''
    command = "youtube"
    aliases = ["yt", ]

    def __init__(self, message):
        super().__init__(message)

        self.subcommands_map = {}
        for cmd in YoutubeMusicFunctions.__dict__.values():
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
        return YoutubeMusic(message).get_delegate_command()


class YoutubeMusicFunctions(object):
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
        aliases = ["q", "add", ]
        silent_permissions = True

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        def _get_server_default_vc(self):
            try:
                return MusicConfiguration.get(server=self._raw_message.server.id).default_channel_id
            except MusicConfiguration.DoesNotExist as e:
                return None

        @staticmethod
        def _is_yt_url(url):
            return url.startswith("http") and "youtube" in url

        @staticmethod
        def _search_yt(query):
            query = urllib.parse.quote(query)
            soup = BeautifulSoup(
                urllib.request.urlopen("https://www.youtube.com/results?search_query={}".format(query)).read(),
                "html.parser"
            )
            results = []
            for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                results.append(('https://www.youtube.com{}'.format(vid["href"]), vid["title"]))
            return results

        @staticmethod
        async def _get_title_from_url(url):
            soup = BeautifulSoup(
                urllib.request.urlopen(url).read(),
                "html.parser"
            )
            return soup.find(id="eow-title")["title"]

        async def _after_notification(self, track):
            await BOT.send_message("Finished playing **{track}**, queued by **{user}**".format(
                track=track.title,
                user=track.queued_by
            ), self._raw_message.channel)

            next_ = _players[self._raw_message.server.id].next_track()
            if next_ is not None:
                await BOT.send_message("Now playing {track}, queued by {user}".format(
                    track=next_.title,
                    user=next_.queued_by
                ), next_.queued_in_channel)

        def _song_after(self):
            _players[self._raw_message.server.id].state = STATE.STOPPED
            coro = self._after_notification(_players[self._raw_message.server.id].now_playing)
            fut = asyncio.run_coroutine_threadsafe(coro, BOT.loop)
            fut.result()

        @overrides(Command)
        async def make_response(self):
            if not BOT.is_voice_connected(self._raw_message.server):
                if self.invoker.voice.voice_channel is None:
                    vc = self._raw_message.server.get_channel(self._get_server_default_vc())
                    if vc is None:
                        logger.debug("Can't queue song because invoker isn't in a voice channel and server doesn't have a default")
                        raise NoVoiceChannelError(
                            "You need to be in a voice channel or the server should have a default channel",
                            mention=self.invoker.mention
                        )
                    voice_conn = await BOT.join_voice_channel(vc)
                else:
                    vc = self.invoker.voice.voice_channel
                    voice_conn = await BOT.join_voice_channel(vc)
            else:
                voice_conn = BOT.voice_client_in(self._raw_message.server)

            if self._raw_message.server.id not in _players.keys():
                _players[self._raw_message.server.id] = YoutubePlayer(voice_conn)
            player = _players[self._raw_message.server.id]

            if self._is_yt_url(self.params[0]):
                logger.debug("Parameter is a YouTube URL, queueing song directly")
                url, track_name = self.params[0], await self._get_title_from_url(self.params[0])
            else:
                query = " ".join(self.params)
                logger.debug("Searching YouTube for {}".format(query))
                url, track_name = self._search_yt(query)[0]

            self.response = "**{track_name}** queued by **{user_name}**".format(
                track_name=track_name,
                user_name=self.invoker.name
            )

            await player.queue(
                url,
                queued_by=self.invoker,
                queued_in_channel=self._raw_message.channel,
                title=track_name,
                after=self._song_after
            )

            logger.debug("Player state is {}".format(player.state))
            if player.state != STATE.PLAYING:
                track = await player.play()
                await BOT.send_message("Now playing {track_name}, queued by {user}".format(
                    queue_response=self.response,
                    chunk_marker=self.response_chunk_marker,
                    track_name=track.title,
                    user=track.queued_by
                ), self._raw_message.channel)

    class NextSong(Command):
        command = "next"
        aliases = ["n", ]
        silent_permissions = True

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        @overrides(Command)
        async def make_response(self):
            if self._raw_message.server.id not in _players.keys():
                self.response = "No track currently playing!"
                return

            if len(_players[self._raw_message.server.id].queued) < 1:
                self.response = "No more songs in queue!"
                return

            track = await _players[self._raw_message.server.id].next_track()
            self.response = "Now playing **{track}**, queued by **{user}**".format(
                track=track.title,
                user=track.queued_by,
            )

    class CurrentPlaylist(Command):
        command = "playlist"
        aliases = ["pl", ]

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        @overrides(Command)
        async def make_response(self):
            if self._raw_message.server.id not in _players.keys():
                self.response = "No music currently playing on this server"
                return

            if len(_players[self._raw_message.server.id].queued) < 1:
                self.response = "No upcoming songs!"
                return

            upcoming = ""
            for track in _players[self._raw_message.server.id].queued:
                upcoming += "♦ **{track}**, queued by **{user}**\n".format(
                    track=track.title,
                    user=track.queued_by,
                )

            self.response = "{upcoming}".format(upcoming=upcoming)

    class Stop(Command):
        command = "stop"
        aliases = ["s", ]

        def __init__(self, message):
            super().__init__(message)

        @overrides(Command)
        async def make_response(self):
            if self._raw_message.server.id not in _players.keys():
                self.response = "No music player active on this server!"
                return

            await _players[self._raw_message.server.id].stop()
            self.response = "Music player stopped"

    class Destroy(Command):
        command = "quit"
        aliases = ["destory", "d", ]

        def __init__(self, message):
            super().__init__(message)

        @overrides(Command)
        async def make_response(self):
            if self._raw_message.server.id not in _players.keys():
                self.response = "No music player active on this server!"
                return

            await _players[self._raw_message.server.id].destroy()

    class GetLink(Command):
        command = "link"
        aliases = ["url", ]

        def __init__(self, message):
            super().__init__(message)

        @overrides(Command)
        async def make_response(self):
            if self._raw_message.server.id not in _players.keys():
                self.response = "No music player active on this server!"
                return

            if _players[self._raw_message.server.id].state != STATE.PLAYING:
                self.response = "No track is currently playing!"
                return

            self.response = "{}".format(_players[self._raw_message.server.id].player.url)
