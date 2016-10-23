# coding: utf-8

"""
Created on 2016-10-20
@author: naoey
"""

import logging
import json
import datetime
import time
import requests

import config

from errors import *
from models import *
from commands import *
from utils import *

logger = logging.getLogger(__name__)

_API_KEY = None
_api = None
if _API_KEY is None:
    with open(config.PATHS["osu_creds"], "r") as cf_r:
        _API_KEY = json.load(cf_r)["api_key"]

if _api is None:
    _api = OsuAPI(_API_KEY)


class OsuCommand(Command):
    command = "osu"

    def __init__(self, message):
        super().__init__(message)

        self.subcommands_map = {}
        for cmd in OsuFunctions.__dict__.values():
            if isinstance(cmd, type) and issubclass(cmd, Command):
                if len(cmd.command) > 0:
                    self.subcommands_map[cmd.command] = cmd
                    for each in cmd.aliases:
                        self.subcommands_map[each] = cmd

    def get_delegate_command(self):
        if len(self.params) == 0:
            return OsuFunctions.UserInfo(self._raw_message)
        if len(self.params) > 0 and self.params[0] in self.subcommands_map.keys():
            return self.subcommands_map[self.params[0]](self._raw_message)

    @classmethod
    async def create_command(cls, message):
        return OsuCommand(message).get_delegate_command()


class OsuFunctions(object):
    class SetName(Command):
        command = "setname"
        aliases = ["setn", ]

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        @overrides(Command)
        async def make_response(self):
            await super().make_response()

            if len(self.params) == 1:
                username = self.params[0]
            else:
                username = " ".join(self.params)

            User.get_or_create(user_id=self.invoker.id, defaults={
                "user_id": self.invoker.id,
                "user_name": self.invoker.name,
            })[0]

            new_data = {
                "username": username,
                "userid": None,
                "discord_user": self.invoker.id,
                "avatar": None,
                "date_registered": datetime.datetime.now(),
                "server_registered": self.source_channel.server.id,
                "channel_registered": self.source_channel.id,
                "last_update_data": None,
                "last_updated": None,
            }

            osuuser, created = OsuUser.get_or_create(defaults=new_data, discord_user=self.invoker.id)

            if not created:
                for field, value in new_data.items():
                    if field == "discord_user":
                        continue

                    setattr(osuuser, field, value)

                osuuser.save()
                self.response = "{sender}\nUpdated your osu! username to {name} 👍".format(
                    sender=self.invoker.mention,
                    name=username,
                )
            else:
                self.response = "{sender}\nStored your osu! username as {name} 👍".format(
                    sender=self.invoker.mention,
                    name=new_data["username"],
                )

    class UserInfo(Command):
        command = "player"
        aliases = ["p", ]

        def __init__(self, message):
            super().__init__(message)

            self.params = self.params[1:]

        @overrides(Command)
        async def make_response(self):
            await super().make_response()

            self.response = "User info goes here"


class OsuAPI(object):
    base_url = "https://osu.ppy.sh/"

    def __init__(self, api_key=None):
        if api_key is None:
            raise ValueError("No API key given")

        self.__api_key = api_key

    @staticmethod
    def _raise_status(response):


    def _base_request(self, url, **kwargs):
        params = {k: v for k, v kwargs.items()}
        r = requests.get(url=self.base_url + url, params=params)
