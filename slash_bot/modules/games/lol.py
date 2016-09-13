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
        summoner, region = await _parse_username_region(params)

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

    async def cmd_summoner(self, sender, channel, params):
        summoner, region = await _delegate.get_summoner_region(sender, params)

        if region not in LeagueOfLegends.valid_regions:
            raise errors.SlashBotValueError("Unkown region {}".format(region))

        riotapi.set_region(region)

        try:
            summoner = riotapi.get_summoner_by_name(summoner)

        except cassiopeia.type.api.exception.APIError as apie:
            if apie.error_code == 404:
                raise errors.SlashBotValueError("Summoner {} not found on region {}".format(summoner, region))
            else:
                raise errors.ThirdPartyAPIError("There was an error in communicating with the Riot API!")

        await BOT.send_message(channel, summoner)

    async def cmd_game(self, sender, channel, params):
        summoner, region = await _delegate.get_summoner_region(sender, params)
        game = await _delegate.get_current_game(summoner, region)

        if game is None:
            await BOT.send_message(channel, "{} is not in game\n{}".format(summoner, sender.mention))
        else:
            await BOT.send_message(channel, game+"\n{}".format(sender.mention))

    async def cmd_test_game(self, sender, channel, params):
        riotapi.set_region("NA")
        summoner = riotapi.get_summoner_by_name("Asat0rr")
        last_match = summoner.recent_games()[0]
        last_match = riotapi.get_match(last_match.id)
        await BOT.send_message(channel, await _delegate._collate_match(last_match))


class LeagueOfLegendsFunctions(object):
    async def get_summoner_region(self, discord_user, params):
        if len(params) <= 1:
            if len(params) == 0:
                uid = discord_user.id
                try:
                    riotuser = RiotUser.get(user=uid)
                    summoner, region = riotuser.summoner_name, riotuser.region
                except RiotUser.DoesNotExist:
                    raise errors.SlashBotValueError("{} no summoner names have been stored for this user."
                                                    " They must `,lol setname` first.".format(discord_user.mention))

            elif len(params) == 1 and params[0].startswith("<@"):
                uid = params[0][1:-1][1:]

                try:
                    riotuser = RiotUser.get(user=uid)
                    summoner, region = riotuser.summoner_name, riotuser.region
                except RiotUser.DoesNotExist:
                    raise errors.SlashBotValueError("{} no summoner names have been stored for this user."
                                                    " They must `,lol setname` first.".format(discord_user.mention))

            else:
                raise errors.CommandFormatError("You didn't give me enough details. Expected `<user/summoner name> <region>`")

        else:
            summoner, region = await self._parse_username_region(params)

        return (summoner, region)

    async def _parse_username_region(self, params):
        if params[0].startswith("\"") or params[0].startswith("'"):
            terminus = params[0][0]
            summoner = params.pop(0)

            try:
                if not summoner.endswith(terminus):
                    while not params[0].endswith(terminus):
                        summoner += " "+params.pop(0)
                    summoner += " "+params.pop(0)

                region = params.pop(0)
                summoner = summoner[1:-1]

            except IndexError:
                raise errors.CommandFormatError("Error understanding what you said. Did you miss any quotes?")

        else:
            region = params[-1]
            params = params[:-1]
            summoner = " ".join(params)

        return (summoner, region)

    async def _collate_match(self, match, brief=True):
        collated = {}

        red_team = []
        blue_team = []

        red_team_raw = match.red_team
        blue_team_raw = match.blue_team

        if red_team_raw.winner:
            collated["winner"] = "RED"
        else:
            collated["winner"] = "BLUE"

        collated["general"] = {
            "RED_BARONS": red_team_raw.baronKills,
            "BLUE_BARONS": blue_team_raw.baronKills,
            "RED_TEAM_TOWER_KILLS": red_team_raw.towerKills,
            "BLUE_TEAM_TOWER_KILLS": blue_team_raw.towerKills,
            "DURATION": match.matchDuration/60,
        }

        champions = [player.championId for player in match.participants]
        champions = list(set(champions))
        champion_names = riotapi.get_champions_by_id(champions)
        mapped_champions = {}

        for id_, name in zip(champions, champion_names):
            mapped_champions[id_] = name

        summoner_spells = []
        for player in match.participants:
            summoner_spells.append(player.spell1Id)
            summoner_spells.append(players.spell2Id)
        summoner_spells = list(set(summoner_spells))
        summoner_spell_names = riotapi.get_summoner_spells_by_id(summoner_spells)
        mapped_spells = {}

        for id_, name in zip(summoner_spells, summoner_spell_names):
            mapped_spells[id_] = name

        items = [y for x, y in player.stats.__dict__.items() if y != 0 and re.match("^item[0-6]$")]
        items = list(set(items))
        item_names = riotapi.get_items_by_id(items)
        mapped_items = {}

        for id_, name in zip(items, item_names):
            mapped_items[id_] = name

        for player in match.participants:
            collated_player = {
                "summoner_name": None,
                "champion": mapped_champions[player.championId],
                "rank": player.highestAchievedSeasonTier,
                "summoner_spells": [
                    mapped_spells[player.spell1Id],
                    mapped_spells[player.spell2Id],
                ],
                "items": list([mapped_items[y] for x, y in player.stats.__dict__.items() if y != 0 and re.match("^item[0-6]$")]),
                "stats": {
                    "kda": "{}/{}/{}".format(player.stats.kills, player.stats.deaths, player.stats.assists),
                    "creep_score": player.stats.minionsKilled+player.stats.neutralMinionsKilled,
                    "gold": "{}/{}".format(player.stats.goldEarned, player.stats.goldSpent),
                    "killing_spree": player.stats.largestKillingSpree,
                    "multi_kill": player.stats.largestMultiKill,
                    "damage": "{}/{}".format(player.stats.totalDamageDealtToChampions, player.stats.totalDamageDealt),
                    "wards": player.stats.wardsPlaced,
                },
            }

            if player.teamId == 100:
                red_team.append(collated_player)
            elif player.teamId == 200:
                blue_team.append(collated_player)

        collated["red_team"] = red_team
        collated["blue_team"] = blue_team

        return collated

    async def get_player_summary(self, summoner_id, region):
        riotapi.set_region(region)
        summoner = riotapi.get_summoner_by_id(summoner_id)
        last_game = summoner.recent_games()[0]
        last_game = riotapi.get_match(last_game.gameId, include_timeline=False)
        last_game = self._collate_match(last_game)

        summary = {}

        general = {}
        matches = {}
        champions = {}
        ranked = {}

        general["name"] = summoner.name
        general["level"] = summoner.level

        # TODO: Finish player summary

    async def get_current_game(self, summoner_id, region):
        riotapi.set_region(region)
        game = riotapi.get_current_game(summoner_id)

        if game is None:
            return game

        red_team = {}
        blue_team = {}
        general = {}


class Responses:
    PLAYER_SUMMARY = (
        "```py\n"
        "Summoner name: {}\n"
        "Summoner level: {}\n"
        "Region: {}\n"
        "Ranked games played: {} ({} won, {} KDA)\n"
        "Favourite champion: {} ({} plays, {} wins, {} KDA)\n"
        "Favourite lane: {}\n"
        "```\n"
    )

    LIVE_GAME_SUMMARY = (
        "**Red Team** - {}%\n"
        "• TOP: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• MID: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• JUNGLE: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• BOT: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• SUPPORT: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "----------------\n"
        "**Blue Team** - {}%\n"
        "• TOP: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• MID: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• JUNGLE: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• BOT: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
        "• SUPPORT: {} ({})\n\t{} played, {}% wins, {} KDA\n\tSummoner spells: {} {}\n\tMasteries: {}-{}-{}\n"
    )

    MATCH_SUMMARY = (
        ""
    )
