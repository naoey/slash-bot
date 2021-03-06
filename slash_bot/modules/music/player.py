# coding: utf-8

"""
Created on 2016-11-22
@author: naoey
"""

import logging
import datetime
import json

from enum import Enum
from abc import ABCMeta, abstractmethod

import config

from errors import *
from models import *
from utils import *

logger = logging.getLogger(__name__)


class STATE(Enum):
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class MusicPlayer(metaclass=ABCMeta):
    """Base player class."""
    def __init__(self):
        self.queued = Playlist()

    @abstractmethod
    async def queue(self, **kwargs):
        pass

    @abstractmethod
    async def play(self):
        pass

    @abstractmethod
    async def pause(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def next_track(self):
        pass

    @abstractmethod
    async def previous_track(self):
        pass

    @abstractmethod
    async def destroy(self):
        pass


class YoutubePlayer(MusicPlayer):
    '''A player that streams from YouTube using discord.py's `get_ytdl_player` player.'''
    def __init__(self, voice_conn=None):
        if voice_conn is None or type(voice_conn).__name__ != "VoiceClient":
            raise ValueError("Can't create a YoutubePlayer without a valid player.")

        super().__init__()
        self.__voice_conn = voice_conn
        self.player = None
        self.state = STATE.STOPPED

    async def queue(self, uri, **kwargs):
        self.queued.append(Track(yt_uri=uri, **kwargs))
        logger.debug("Queue is {}".format(self.queued))

    async def play(self):
        if len(self.queued) < 1:
            raise MusicError("No more tracks in playlist!")

        if self.state != STATE.PLAYING:
            self.now_playing = self.queued.pop(0)
            self.player = await self.__voice_conn.create_ytdl_player(self.now_playing.yt_uri, after=self.now_playing.after)
            self.player.start()
            logger.debug("Player is {} and state is {}".format(self.player, self.player.is_playing()))
            self.state = STATE.PLAYING
            return self.now_playing

    async def pause(self):
        if self.state == STATE.PLAYING:
            self.player.pause()
            self.state = STATE.PAUSED

    async def stop(self):
        if self.state == STATE.PLAYING:
            self.player.stop()
            self.player = None
            self.state = STATE.STOPPED

    async def next_track(self):
        if self.queued.length() > 0:
            if self.player.is_playing():
                await self.stop()
                await self.play()

        return self.now_playing

    async def previous_track(self):
        logger.info("Previous functionality not implemented yet")

    async def destroy(self):
        if self.player is not None and self.player.is_playing():
            await self.stop()
        await self.__voice_conn.disconnect()


class LocalPlayer(MusicPlayer):
    '''A player that streams from the local file system using discord.py's `get_ffmpeg_player` player.'''
    pass


class Track(object):
    """A track which is played by a `MusicPlayer`"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Playlist(list):
    """A collection of `Track` objects."""
    def length(self):
        return len(self)
