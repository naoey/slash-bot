# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import json
import cassiopeia
import datetime, time
import re

import config
import errors

from cassiopeia import riotapi, baseriotapi
from models import *

BOT = config.GLOBAL["bot"]
_delegate = None


class LeagueOfLegends(object):

    valid_regions = [
        "NA",
        "EUW",
        "EUNE",
        "JP",
        "KR",
        "BR",
        "RU",
        "LAN",
        "LAS",
        "TR",
    ]

    def __init__(self):
        global _delegate

        with open(config.PATHS["rito_creds"], "r") as cf_r:
            riotapi.set_api_key(json.load(cf_r)["api_key"])

        if _delegate is None:
            _delegate = LeagueOfLegendsFunctions()

    async def cmd_setname(self, sender, channel, params):
        summoner, region = await _delegate.parse_username_region(params)

        if region not in LeagueOfLegends.valid_regions:
            raise errors.SlashBotValueError("Unkown region {}".format(region))

        user = User.get_or_create(user_id=sender.id, defaults={
            "user_id": sender.id,
            "user_name": sender.name,
        })[0]

        new_data = {
            "summoner_name": summoner,
            "region": region,
            "user": user.user_id,
            "date_registered": datetime.datetime.now(),
            "server_registered": sender.server.id,
            "channel_registered": channel.id,
            "last_update_data": None,
            "last_updated": None,
        }

        riotuser, created = RiotUser.get_or_create(defaults=new_data, user=sender.id, region=region)

        if not created:
            for field, value in new_data.items():
                if field == "user":
                    continue

                setattr(riotuser, field, value)

            await BOT.send_message(channel, "{}\nUpdated your LoL username to {} on region {} 👍".format(sender.mention, summoner, region))
        else:
            await BOT.send_message(channel, "{}\nStored your LoL name on {} 👍".format(sender.mention, region))

        riotuser.save()

    async def cmd_player(self, sender, channel, params):
        summoner = await _delegate.get_summoner_info(sender, params)
        await BOT.send_message(channel, summoner)


class LeagueOfLegendsFunctions(object):
    async def get_summoner_info(self, discord_user, params):
        if len(params) <= 1:
            if len(params) == 0:
                uid = discord_user.id
                try:
                    riotuser = RiotUser.get(user=uid)
                    summoner = {
                        "name": riotuser.summoner_name,
                        "id": riotuser.summoner_id,
                        "region": riotuser.region,
                    }
                except RiotUser.DoesNotExist:
                    raise errors.SlashBotValueError("{} no summoner names have been stored for this user."
                                                    " They must `,lol setname` first.".format(discord_user.mention))

            elif len(params) == 1 and params[0].startswith("<@"):
                uid = params[0][1:-1][1:]

                try:
                    riotuser = RiotUser.get(user=uid)
                    summoner = {
                        "name": riotuser.summoner_name,
                        "id": riotuser.summoner_id,
                        "region": riotuser.region,
                    }
                except RiotUser.DoesNotExist:
                    raise errors.SlashBotValueError("{} no summoner names have been stored for this user."
                                                    " They must `,lol setname` first.".format(discord_user.mention))

            else:
                raise errors.CommandFormatError("You didn't give me enough details. Expected `<user/summoner name> <region>`")

        else:
            name, region = await self.parse_username_region(params)
            summoner = {
                "name": name,
                "id": None,
                "region": region,
            }

        return summoner

    async def parse_username_region(self, params):
        if params[0].startswith("\"") or params[0].startswith("'"):
            terminus = params[0][0]
            name = params.pop(0)

            try:
                if not name.endswith(terminus):
                    while not params[0].endswith(terminus):
                        name += " "+params.pop(0)
                    name += " "+params.pop(0)

                region = params.pop(0)
                name = name[1:-1]

            except IndexError:
                raise errors.CommandFormatError("Error understanding what you said. Did you miss any quotes?")

        else:
            region = params[-1]
            params = params[:-1]
            name = " ".join(params)

        return (name, region)

    async def match_details(self, match_id):
        pass

    async def recent_games(self, summoner_id):
        pass

    async def player_summary(self, summoner_id):
        pass


class Responses:
    pass
