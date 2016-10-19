# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import datetime

import config

from errors import *
from models import *
from commands import *
from utils import *

logger = logging.getLogger(__name__)

BOT = config.GLOBAL["bot"]

_alive_listeners = {}


class SlowMode(Command):
    command = "slowmode"
    aliases = ["sm", ]

    class Slower(object):
        def __init__(self, channel=None, interval=5, user=None):
            self.interval = 5
            self.channel = channel
            self.user = user["id"] if user is not None else None
            self.uname = user["name"] if user is not None else None
            self.slowid = channel.id + "_" + user["id"] if user is not None else None

            self._subscription = BOT.subscribe_channel_messages(channel.id, self.clean)

            self.last_message_time = None

        async def clean(self, message):
            if self.last_message_time is None:
                if self.user is not None:
                    if message.author.id != self.user:
                        return
                self.last_message_time = message.timestamp
                return

            if (message.timestamp - self.last_message_time).total_seconds() < self.interval:
                if self.user is not None:
                    if message.author.id != self.user:
                        return
                if message.channel.id == self.channel.id and message.author.id != config.GLOBAL["discord"]["bot_id"]:
                    await BOT.delete_message(message)
            self.last_message_time = message.timestamp

        async def end(self):
            BOT.unsubscribe_channel_messages(self._subscription)

    @overrides(Command)
    async def make_response(self):
        if len(self.params) <= 1:
            if self.source_channel.id in _alive_listeners.keys():
                await _alive_listeners[self.source_channel.id].end()
                self.response = "Slowmode disabled"
                del _alive_listeners[self.source_channel.id]
            else:
                if len(self.params) < 1:
                    _alive_listeners[self.source_channel.id] = (SlowMode.Slower(self.source_channel))
                    self.response = "Slowmode enabled"
                if len(self.params) == 1:
                    _alive_listeners[self.source_channel.id] = (SlowMode.Slower(self.source_channel, interval=self.params[0]))
                    self.response = "Slowmode enabled with limit as 1 message per {} seconds".format(self.params[0])

        elif len(self.params) == 2:
            uid = self.params[1][2:-1]
            uname = next((x.name for x in self._raw_message.mentions if x.id == uid))
            slowid = self.source_channel.id + "_" + uid

            if slowid in _alive_listeners.keys() and _alive_listeners[self.source_channel.id].slowid == slowid:
                await _alive_listeners[slowid].end()
                self.response = "Slowmode disabled for {}".format(_alive_listeners[self.source_channel.id].uname)
                del _alive_listeners[slowid]
            else:
                _alive_listeners[self.source_channel.id] = (SlowMode.Slower(
                    self.source_channel,
                    interval=self.params[0],
                    user={
                        "id": uid,
                        "name": uname
                    }))
                self.response = "Slowmode enabled with limit as 1 message per {} seconds for {}".format(
                    self.params[0],
                    uname,
                )
