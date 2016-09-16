# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import json
import riotwatcher
import datetime, time
import re

import config
# TODO: Import all errors into namespace instead of qualifying every time
import errors

from models import *

BOT = config.GLOBAL["bot"]
_delegate = None

api = None

_API_KEY = None

REGIONS = {
    "NA": "North America",
    "EUW": "Europe West",
    "EUNE": "Europe Nordic & East",
    "JP": "Japan",
    "RU": "Russia",
    "KR": "Korea",
    "LAS": "Latin America South",
    "LAN": "Latin America North",
    "TK": "Turkey",
    "BR": "Brazil",
    "OCE": "Oceania",
}

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
        global _API_KEY
        global api

        if _API_KEY is None:
            with open(config.PATHS["rito_creds"], "r") as cf_r:
                _API_KEY = json.load(cf_r)["api_key"]

        if _delegate is None:
            _delegate = LeagueOfLegendsFunctions()

        if api is None:
            api = riotwatcher.RiotWatcher(_API_KEY)

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

        if summoner["id"] is None:
            try:
                rito_resp = api.get_summoner(summoner["name"])
            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    raise errors.SlashBotValueError("Summoner {} not found on region {}".format(summoner["name"], summoner["region"]))

            summoner["id"] = rito_resp["id"]

            r = RiotUser.update(summoner_id=rito_resp["id"]).where(
                    (RiotUser.summoner_name == summoner["name"]) & (RiotUser.region == summoner["region"])
                ).execute()

            if r < 1:
                logging.debug(
                    ("Local player info/summoner id wasn't updated for summoner {} on {}."
                    "Either this user isn't stored locally or there was an error updating.").format(
                        summoner["name"],
                        summoner["region"]
                    )
                )

        # TODO: Handle 404 for non existent player
        player_info = await _delegate.player_summary(summoner["id"], summoner["region"])

        await BOT.send_message(channel, Responses.PLAYER_SUMMARY.format(**player_info))


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
                    raise errors.SlashBotValueError(
                        "{} no summoner names have been stored for this user."
                        " They must `,lol setname` first.".format(discord_user.mention)
                    )

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
                    raise errors.SlashBotValueError(
                        "{} no summoner names have been stored for this user."
                        " They must `,lol setname` first.".format(discord_user.mention)
                    )

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

    async def match_details(self, match_id, region):
        pass

    async def recent_games(self, summoner_id, region):
        pass

    async def player_summary(self, summoner_id, region):
        # try:
        #     user = RiotUser.get(summoner_id=summoner_id)
        #
        #     if user.last_updated is not None and (datetime.datetime.now()-user.last_updated).total_seconds()/3600 < 5:
        #         return json.loads(user.last_update_data)
        #
        # except RiotUser.DoesNotExist:
        #     logging.debug("No local user stored, proceeding with just summoner id")

        summoner = api.get_summoner(_id=summoner_id, region=region)

        collated = {}
        collated["name"] = summoner["name"]
        collated["level"] = summoner["summonerLevel"]
        collated["region"] = REGIONS[region]
        collated["recent"] = {
            "name": None,
            "plays": 0,
            "wins": 0,
            "kda": 0,
        }
        collated["mastery"] = {
            "level": 0,
            "plays": 0,
            "score": 0,
        }
        collated["normal_wins"] = 0
        collated["ranked"] = {
            "league": None,
            "division": "",
            "points": 0,
            "wins": 0,
            "losses": 0,
            "fav": {
                "name": None,
                "plays": 0,
                "wins": 0,
                "kda": 0,
        },
        "kills_avg": 0,
        "deaths_avg": 0,
        "assists_avg": 0,
        "kills": 0,
        "deaths": 0,
        "assists": 0,
        "largest_spree": 0,
        "double": 0,
        "triple": 0,
        "quadra": 0,
        "penta": 0,
        "cs": 0,
        "gold": 0,
        "towers": 0,
        }

        try:
            stats = api.get_stat_summary(summoner_id, region=region)

            unranked_stats = [stat_summary for stat_summary in stats["playerStatSummaries"]
                                        if stat_summary["playerStatSummaryType"] == "Unranked"][0]

            collated["normal_wins"] = unranked_stats["wins"]
        except riotwatcher.LoLException as e:
            return collated

        try:
            ranked = api.get_ranked_stats(summoner_id, region=region)

            favourite_champion = max([x for x in ranked["champions"] if x["id"] != 0], key=lambda d: d["stats"]["totalSessionsPlayed"])
            favourite_champion_name = api.static_get_champion(favourite_champion["id"], champ_data="info")
            logging.debug(favourite_champion_name)
            collated["ranked"]["fav"] = {
                "name": favourite_champion_name["name"],
                "plays": favourite_champion["stats"]["totalSessionsPlayed"],
                "wins": favourite_champion["stats"]["totalSessionsWon"],
                "kda": "{}/{}/{}".format(
                    favourite_champion["stats"]["totalChampionKills"],
                    favourite_champion["stats"]["totalDeathsPerSession"],
                    favourite_champion["stats"]["totalAssists"]
                )
            }

            league = api.get_league(summoner_ids=[summoner_id,])
            # TODO: Check why summoner_id is int here
            player_in_league = [x for x in league[str(summoner_id)][0]["entries"] if x["playerOrTeamId"] == str(summoner_id)][0]
            collated["ranked"]["league"] = league[str(summoner_id)][0]["tier"].title()
            collated["ranked"]["division"] = player_in_league["division"]
            collated["ranked"]["points"] = player_in_league["leaguePoints"]
            collated["ranked"]["wins"] = player_in_league["wins"]
            collated["ranked"]["losses"] = player_in_league["losses"]

            ranked_general = [x for x in ranked["champions"] if x["id"] == 0][0]["stats"]
            logging.debug(ranked_general)
            collated["ranked"]["kills_avg"] = round(ranked_general["totalChampionKills"]/ranked_general["totalSessionsPlayed"], 2)
            collated["ranked"]["deaths_avg"] = round(ranked_general["totalDeathsPerSession"]/ranked_general["totalSessionsPlayed"], 2)
            collated["ranked"]["assists_avg"] = round(ranked_general["totalAssists"]/ranked_general["totalSessionsPlayed"], 2)
            collated["ranked"]["kills"] = ranked_general["totalChampionKills"]
            collated["ranked"]["deaths"] = ranked_general["totalDeathsPerSession"]
            collated["ranked"]["assists"] = ranked_general["totalAssists"]
            collated["ranked"]["largest_spree"] = ranked_general["maxLargestKillingSpree"]
            collated["ranked"]["double"] = ranked_general["totalDoubleKills"]
            collated["ranked"]["triple"] = ranked_general["totalTripleKills"]
            collated["ranked"]["quadra"] = ranked_general["totalQuadraKills"]
            collated["ranked"]["penta"] = ranked_general["totalPentaKills"]
            collated["ranked"]["cs"] = ranked_general["totalMinionKills"]
            collated["ranked"]["gold"] = ranked_general["totalGoldEarned"]
            collated["ranked"]["towers"] = ranked_general["totalTurretsKilled"]
        except riotwatcher.LoLException as e:
            return collated

        r = RiotUser.update(last_update_data=json.dumps(collated), last_updated=datetime.datetime.now()).where(
                (RiotUser.summoner_id == summoner_id) & (RiotUser.region == region)
            ).execute()

        if r < 1:
            logging.error("There was an error updating player info for summoner {} {}".format(summoner_id, region))

        return collated


class Responses:
    PLAYER_SUMMARY = (
        "```py\n"
        "Summoner name: {name}\n"
        "Summoner level: {level}\n"
        "Region: {region}\n"
        "Recently played: {recent[name]} ({recent[plays]} plays, {recent[wins]} wins, {recent[kda]} KDA)\n"
        "Highest champion mastery: {mastery[level]} ({mastery[plays]} plays, {mastery[score]} score)\n"
        "Normal games won: {normal_wins}\n"
        "-------\n"
        "Ranked stats\n"
        "-------\n"
        "League: {ranked[league]} {ranked[division]}, {ranked[points]} points\n"
        "Games this season: {ranked[wins]} wins, {ranked[losses]} losses\n"
        "Favourite champion: {ranked[fav][name]} ({ranked[fav][plays]} plays, {ranked[fav][wins]} wins, {ranked[fav][kda]} K/D/A)\n"
        # "Favourite position: {}\n"
        "Average K/D/A: {ranked[kills_avg]}/{ranked[deaths_avg]}/{ranked[assists_avg]}\n"
        "Total K/D/A: {ranked[kills]}/{ranked[deaths]}/{ranked[assists]}\n"
        "Largest killing spree: {ranked[largest_spree]}\n"
        "Double/Triple/Quadra/Penta: {ranked[double]}/{ranked[triple]}/{ranked[quadra]}/{ranked[penta]}\n"
        "Creep score: {ranked[cs]}\n"
        "Gold earned: {ranked[gold]}\n"
        "Towers destroyed: {ranked[towers]}\n"
        #"MMR: {ranked[mmr]}\n"
        "```\n"
    )
