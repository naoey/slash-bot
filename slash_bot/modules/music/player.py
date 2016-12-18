# coding: utf-8

"""
Created on 2016-11-22
@author: naoey
"""

import logging
import datetime
import json

from enum import Enum

import config

from errors impot *
from models import *
from utils import *

logger = logging.getLogger(__name__)


class STATE(Enum):
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class MusicPlayer(object):
    def __init__(self, voice_channel=None):
        if voice_channel is None:
            raise ValueError("No voice channel given")

        self.state = STATE.STOPPED

        self._playlist = []
        self._current_idx = -1

    async def queue(self, **kwargs):
        if url not in kwargs.keys() or kwargs["url"] is None or not _is_yt_url(kwargs["url"]):
            raise ValueError("Invalid URL")

        self._playlist.append(kwargs)
        return True

    async def play(self):
        if url is None:
            return

        if self.state == STATE.PAUSED:
            self.state = STATE.PLAYING

        self.state = STATE.PLAYING
        return True

    async def pause(self):
        if self.state == STATE.PLAYING:
            self.state = STATE.PAUSED

        return True

    async def stop(self):
        if self.state != STATE.STOPPED:
            self.state = STATE.STOPPED

        return True

    async def next(self):
        if self._current_idx + 1 >= self._playlist.length:
            raise SlashBotMusicNoTrackException("No more songs queued!")

        return True

    async def previous(self):
        if self._current_idx - 1 < 0:
            raise SlashBotMusicNoTrackException("This is the first track in queue!")

        return True

    async def destroy(self):
        pass


def _is_yt_url(url):
    return True
