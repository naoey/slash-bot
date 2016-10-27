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


class OsuAPI(object):
    base_url = 'https://osu.ppy.sh/'

    def __init__(self, api_key=None):
        if api_key is None:
            raise ValueError('No API key given')

        self.__api_key = api_key

    class OsuException(Exception):
        error_403 = "Forbidden"
        error_404 = "Not found"

    @staticmethod
    def _raise_status(response):
        if response.status_code == 403:
            raise OsuException(OsuException.error_403)
        elif response.status_code == 404:
            raise OsuException(OsuException.error_404)

    async def _base_request(self, url, **kwargs):
        params = {
            'k': self.__api_key
        }
        for each in kwargs:
            params[each] = kwargs[each]
        r = requests.get(url=self.base_url + url, params=params)
        self._raise_status(r)
        return r.json()

    async def beatmaps(self, **kwargs):
        return await self._base_request(
            'api/get_beatmaps',
            **kwargs
        )

    async def user(self, **kwargs):
        return await self._base_request(
            'api/get_user',
            **kwargs
        )

    async def get_scores(self, **kwargs):
        return await self._base_request(
            'api/get_scores',
            **kwargs
        )

    async def get_user_best(self, **kwargs):
        return await self._base_request(
            'api/get_user_best',
            **kwargs
        )

    async def get_user_recent(self, **kwargs):
        return await self._base_request(
            'api/get_user_recent',
            **kwargs
        )

    async def get_match(self, **kwargs):
        return await self._base_request(
            'api/get_match',
            **kwargs
        )

    async def get_replay(self, **kwargs):
        return await self._base_request(
            'api/get_replay',
            **kwargs
        )


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
        if len(self.params) == 0 or (len(self.params) > 0 and self.params[0] not in self.subcommands_map.keys()):
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

            if len(self.params) == 0:
                try:
                    osuuser = OsuUser.get(discord_user=self.invoker.id)
                    username = osuuser.userid if osuuser.userid is not None else osuuser.username
                    usertype = "id" if osuuser.userid is not None else "string"
                except OsuUser.DoesNotExist:
                    username = self.invoker.name
                    usertype = "string"
            elif len(self.params) == 1:
                username = self.params[0]
                usertype = "string"
            elif len(self.params) == 1 and self.params[0].startswith("<@"):
                uid = uid_from_mention(self.params[0])
                try:
                    osuuser = OsuUser.get(discord_user=uid)
                    username = osuuser.userid if osuuser.userid is not None else osuuser.username
                    usertype = "id" if osuuser.userid is not None else "string"
                except OusUser.DoesNotExist:
                    username = next((x.name for x in self._raw_message.mentions if x.id == uid))
                    usertype = "string"
            else:
                username = " ".join(self.params)
                usertype = "string"

            r = await _api.user(u=username, type=usertype)
            if len(r) < 1:
                self.response = "Couldn't find a user by name {}".format(username)
                return
            r = r[0]
            best_r = await _api.get_user_best(u=username, type=usertype, limit=1)
            best_r = best_r[0]
            best_beatmap_r = await _api.beatmaps(b=best_r["beatmap_id"], limit=1)
            best_beatmap_r = best_beatmap_r[0]
            self.response = (
                "{profile_url}\n"
                "{avatar_url}\n"
                "```\n"
                "User: {user_name}\n"
                "Rank: #{global_rank}, #{country_rank} {country}\n"
                "Performance: {pp} pp\n"
                "Accuracy: {acc}%\n"
                "Best play: {best_map}, {best_pp} pp\n"
                "Plays: {total_plays}, Score: {total_score}, Hits: {total_hits}\n"
                "```"
            ).format(
                user_name=r["username"],
                global_rank=r["pp_rank"],
                country_rank=r["pp_country_rank"],
                country=r["country"],
                pp=r["pp_raw"],
                acc=round(float(r["accuracy"]), 2),
                best_map="{artist} - {name} [{version}] {stars} stars".format(
                    artist=best_beatmap_r["artist"],
                    name=best_beatmap_r["title"],
                    version=best_beatmap_r["version"],
                    stars=round(float(best_beatmap_r["difficultyrating"]), 2)
                ),
                best_pp=best_r["pp"],
                total_plays=r["playcount"],
                total_score=r["total_score"],
                total_hits=0,
                profile_url="https://osu.ppy.sh/u/{}".format(r["user_id"]),
                avatar_url="https://a.ppy.sh/{}".format(r["user_id"]),
            )

    class TopPlays(Command):
        command = "top"

        @overrides(Command)
        async def make_response(self):
            pass
