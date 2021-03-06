# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import datetime

from discord import Forbidden, NotFound

import config

from errors import *
from models import *
from commands import *
from utils import *

logger = logging.getLogger(__name__)

BOT = config.GLOBAL["bot"]

_alive_slowers = {}


class SlowMode(Command):
    command = "slowmode"
    aliases = ["sm", ]
    required_permissions = [PERMISSIONS.SERVER_ADMIN, ]

    def __init__(self, message):
        super().__init__(message)

        for key in _alive_slowers.keys():
            if "_" in key and key.split("_")[1] == self.invoker.id:
                # This user is being slowed, make permissions silent on this command to prevent proxy spam through bot
                self.silent_permissions = True

    class Slower(object):
        def __init__(self, channel=None, interval=5, user=None, slowed_by=None):
            self.interval = int(interval)
            self.channel = channel
            self.user = user["id"] if user is not None else None
            self.uname = user["name"] if user is not None else None
            self.slowid = channel.id + "_" + user["id"] if user is not None else None
            self.slowed_by = slowed_by

            self._subscription = BOT.subscribe_channel_messages(channel.id, self.clean)

            self.last_message_time = None
            self.enabled = True

            if self.slowid is not None:
                _alive_slowers[self.slowid] = self
            else:
                _alive_slowers[self.channel.id] = self

        async def clean(self, message):
            if not self.enabled:
                return

            if message.content.startswith(config.BOT_PREFIX):
                first_word = message.content[1:].split(" ")[0]
                if (PermissionsManager.can(message.channel, message.author, permission=PERMISSIONS.SERVER_ADMIN) and
                        (first_word == SlowMode.command or first_word in SlowMode.aliases)):
                    return

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

                if message.channel.id == self.channel.id and message.author.id != config.GLOBAL["bot_id"]:
                    try:
                        await BOT.delete_message(message)
                    except Forbidden:
                        await BOT.send_error(
                            DiscordPermissionError("Somebody stole my powaa to manage messages, I quit ☹"),
                            self.channel
                        )
                        await self.end()
                    except NotFound:
                        pass
            else:
                self.last_message_time = message.timestamp

        async def end(self):
            self.enabled = False
            BOT.unsubscribe_channel_messages(self._subscription)
            if self.slowid is not None:
                del _alive_slowers[self.slowid]
            else:
                del _alive_slowers[self.channel.id]

    @overrides(Command)
    async def make_response(self):
        await super().make_response()

        if not self.source_channel.server.get_member(BOT.user.id).permissions_in(self.source_channel).manage_messages:
            self.response = "{} Gib me permission to manage messages here!".format(self.invoker.mention)
            return

        if len(self.params) == 0:
            if self.source_channel.id in _alive_slowers.keys():
                await _alive_slowers[self.source_channel.id].end()
                self.response = "Slow mode disabled, spemmmm!"
            else:
                existing_user_slows = []
                for key, value in _alive_slowers.items():
                    if key.split("_")[0] == self.source_channel.id:
                        existing_user_slows.append(value)
                for each in existing_user_slows:
                    await each.end()

                SlowMode.Slower(self.source_channel, slowed_by=self.invoker.id)
                self.response = "Slow mode enabled, shush"

        elif len(self.params) == 1:
            if self.params[0].isdigit():
                if self.source_channel.id in _alive_slowers.keys():
                    await _alive_slowers[self.source_channel.id].end()
                    self.response = "Slow mode disabled, spemmmm!"
                else:
                    SlowMode.Slower(self.source_channel, self.params[0], slowed_by=self.invoker.id)
                    self.response = "Slow mode enabled, spam limited to once every {} second(s)".format(self.params[0])

            elif self.params[0].startswith("<@"):
                if self.source_channel.id in _alive_slowers.keys():
                    self.response = "The whole channel is slowed already! Disable it to slow per-user."
                    return

                uid = uid_from_mention(self.params[0])
                user = next((x for x in self._raw_message.mentions if x.id == uid), None)
                slowid = self.source_channel.id + "_" + uid

                if slowid in _alive_slowers.keys():
                    await _alive_slowers[slowid].end()
                    self.response = "{} is now free to spam again".format(user.name)
                else:
                    SlowMode.Slower(
                        self.source_channel,
                        user={
                            "id": uid,
                            "name": user.name if user is not None else "",
                        },
                        slowed_by=self.invoker.id,
                    )
                    self.response = "{} is now being spam-limited".format(user.name)

        elif len(self.params) == 2 and self.params[0].startswith("<@") and self.params[1].isdigit():
            if self.source_channel.id in _alive_slowers.keys():
                self.response = "{} the whole channel is slowed already! Disable it to slow per-user.".format(self.invoker.mention)
                return

            uid = uid_from_mention(self.params[0])
            user = next((x for x in self._raw_message.mentions if x.id == uid), None)
            slowid = self.source_channel.id + "_" + uid

            if slowid in _alive_slowers.keys():
                await _alive_slowers[slowid].end()
                self.response = "{} is now free to spam again".format(user.name)
            else:
                SlowMode.Slower(
                    self.source_channel,
                    interval=self.params[1],
                    user={
                        "id": uid,
                        "name": user.name if user is not None else "",
                    },
                    slowed_by=self.invoker.id,
                )
                self.response = "{} is now being spam-limited to 1 message per {} second(s)".format(user.name, self.params[1])

        else:
            self.response = "Bad command"


class SlowList(Command):
    command = "slowlist"
    aliases = ["sl", "sml", ]
    silent_permissions = True

    @overrides(Command)
    async def make_response(self):
        slowed_users = {}
        for key, val in _alive_slowers.items():
            if "_" in key and key.split("_")[0] == self.source_channel.id:
                slowed_users[val.user] = {
                    "name": val.uname,
                    "timeout": val.interval,
                }

        if self.invoker.id in slowed_users.keys() and not PermissionsManager.can(self.source_channel, self.invoker, PERMISSIONS.SERVER_ADMIN):
            self.response = None
            return
        else:
            if self.source_channel.id in _alive_slowers.keys():
                self.response = "The whole channel is being slowed"
            elif len(slowed_users) == 0:
                self.response = "Slowmode is disabled on this channel"
            else:
                users = ""
                for each in slowed_users.values():
                    users += "• {} - {} seconds\n".format(each["name"], each["timeout"])

                self.response = "Users currently in slow mode on this channel:\n```py\n{}\n```".format(users)
