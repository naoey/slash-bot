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

from errors import *
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

PLAYER_POSITION = {
    1: "Top",
    2: "Middle",
    3: "Jungle",
    4: "Bot"
}

PLAYER_ROLE = {
    1: "DUO",
    2: "SUPPORT",
    3: "CARRY",
    4: "SOLO",
}

MAPS = {
    1: "Summoner's Rift",
    2: "Summoner's Rift",
    3: "The Proving Grounds",
    4: "Twisted Treeline",
    8: "The Crystal Scar",
    10: "Twisted Treeline",
    11: "Summoner's Rift",
    12: "Howling Abyss",
    14: "Butcher's Bridge",
}

GAME_TYPES = {
    "CUSTOM_GAME": "Custom Game",
    "TUTORIAL_GAME": "Tutorial",
    "MATCHED_GAME": "Matched game",
}

GAME_SUB_TYPES = {
    "NONE": "Custom game",
    "NORMAL":  "Unranked on Summoner's Rift",
    "NORMAL_3x3": "Unranked on Twisted Treeline",
    "ODIN_UNRANKED": "Dominion on Crystal Scar",
    "ARAM_UNRANKED_5v5": "ARAM on Howling Abyss",
    "BOT": "Co-op vs AI 5v5",
    "BOT_3x3": "Co-op vs AI on Twisted Treeline",
    "RANKED_SOLO_5x5": "Ranked on Summoner's Rift",
    "RANKED_TEAM_3x3": "Ranked team on Twisted Treeline",
    "RANKED_TEAM_5x5": "Ranked team on Summoner's Rift",
    "ONEFORALL_5x5": "One For All 5v5",
    "FIRSTBLOOD_1x1": "Snowdown Showdown 1v1",
    "FIRSTBLOOD_2x2": "Snowdown Showdown 2v2",
    "SR_6x6": "Hexakill on Summoner's Rift",
    "URF": "Ultra Rapid Fire",
    "URF_BOT": "Ultra Rapid Fire Co-op vs AI",
    "NIGHTMARE_BOT": "Nightmare Bots",
    "ASCENSION": "Ascension",
    "HEXAKILL": "Hexakill on Twisted Treeline",
    "KING_PORO": "King Poro",
    "COUNTER_PICK": "Nemesis Draft",
    "BILGEWATER": "Black Market Brawlers",
}

# Static data
CHAMPIONS = None
MASTERIES = None
RUNES = None
SUMMONER_SPELLS = None

class LeagueOfLegends(object):
    def __init__(self):
        global _delegate
        global _API_KEY
        global api
        global CHAMPIONS

        if _API_KEY is None:
            with open(config.PATHS["rito_creds"], "r") as cf_r:
                _API_KEY = json.load(cf_r)["api_key"]

        if api is None:
            api = riotwatcher.RiotWatcher(_API_KEY)

        Delegate.refresh_static_data()

        if _delegate is None:
            _delegate = Delegate()

    async def cmd_setname(self, sender, channel, params):
        summoner, region = await _delegate.parse_username_region(params)

        if region not in REGIONS.keys():
            raise SlashBotValueError("Unkown region {}".format(region))

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

            await BOT.send_message(channel, Responses.UPDATED_LOL_USERNAME.format(
                sender=sender.mention,
                name=summoner,
                region=region)
            )
        else:
            await BOT.send_message(channel, Response.STORED_LOL_USERNAME.format(
                name=sender.mention,
                region=region)
            )

        riotuser.save()

    async def cmd_summoner(self, sender, channel, params):
        summoner = await _delegate.get_summoner_info(sender, params)

        player_info = await _delegate.player_summary(summoner["id"], summoner["region"])

        await BOT.send_message(channel, Responses.PLAYER_SUMMARY.format(**player_info))

    async def cmd_game(self, sender, channel, params):
        summoner = await _delegate.get_summoner_info(sender, params)

        game = await _delegate.live_game(summoner["id"], summoner["region"])

        if game is None:
            await BOT.send_message(channel, Responses.NOT_IN_GAME.format(
                name=summoner["name"],
                region=summoner["region"])
            )

        else:
            await BOT.send_message(channel, Responses.LIVE_GAME.format(**game))


class Delegate(object):
    @staticmethod
    def refresh_static_data():
        global CHAMPIONS
        global MASTERIES
        global RUNES
        global SUMMONER_SPELLS

        if CHAMPIONS is None:
            CHAMPIONS = api.static_get_champion_list(region=riotwatcher.NORTH_AMERICA, data_by_id=True, champ_data="all")
            logging.debug("Collected {} champions".format(len(CHAMPIONS["data"])))

        if MASTERIES is None:
            MASTERIES = api.static_get_mastery_list(region=riotwatcher.NORTH_AMERICA, mastery_list_data="all")
            logging.debug("Collected {} masteries".format(len(MASTERIES["data"])))

        if RUNES is None:
            RUNES = api.static_get_rune_list(region=riotwatcher.NORTH_AMERICA, rune_list_data="all")
            logging.debug("Collected {} runes".format(len(RUNES["data"])))

        if SUMMONER_SPELLS is None:
            SUMMONER_SPELLS = api.static_get_summoner_spell_list(region=riotwatcher.NORTH_AMERICA, spell_data="all")
            logging.debug("Collected {} summoner spells".format(len(SUMMONER_SPELLS["data"])))
        #
        # for id_, data in CHAMPIONS["data"].items():
        #     try:
        #         AssetStore.get("lol/icons/champions/{}".format(id_))
        #     except AssetsError:
        #         AssetStore.store(api.get_champion_icon(champion_name=data["image"]["full"]))

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
                    raise SlashBotValueError(
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
                    raise SlashBotValueError(
                        "{} no summoner names have been stored for this user."
                        " They must `,lol setname` first.".format(discord_user.mention)
                    )

            else:
                raise CommandFormatError("You didn't give me enough details. Expected `<user/summoner name> <region>`")

        else:
            name, region = await self.parse_username_region(params)
            summoner = {
                "name": name,
                "id": None,
                "region": region,
            }

        summoner = await self._update_summoner_info(summoner)

        return summoner

    async def _update_summoner_info(self, summoner):
        if summoner["id"] is None:
            try:
                rito_resp = api.get_summoner(summoner["name"])
            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    raise SlashBotValueError("Summoner {} not found on region {}".format(summoner["name"], summoner["region"]))

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
                raise CommandFormatError("Error understanding what you said. Did you miss any quotes?")

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
            "total_mastery": 0,
            "champion": None,
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

        collated = await self._unranked_player_summary(collated, summoner_id, region)
        collated = await self._ranked_player_summary(collated, summoner_id, region)

        r = RiotUser.update(last_update_data=json.dumps(collated), last_updated=datetime.datetime.now()).where(
                (RiotUser.summoner_id == summoner_id) & (RiotUser.region == region)
            ).execute()

        if r < 1:
            logging.error("There was an error updating player info for summoner {} {}".format(summoner_id, region))

        return collated

    async def _unranked_player_summary(self, collated, summoner_id, region):
        try:
            stats = api.get_stat_summary(summoner_id, region=region)

            unranked_stats = [stat_summary for stat_summary in stats["playerStatSummaries"]
                                        if stat_summary["playerStatSummaryType"] == "Unranked"][0]

            collated["normal_wins"] = unranked_stats["wins"]

            recent_games = api.get_recent_games(summoner_id)
            champions_played = {}

            for game in recent_games["games"]:
                if game["subType"] != "BOT":
                    try:
                        champions_played[game["championId"]]["plays"] += 1
                        champions_played[game["championId"]]["kills"] += game["stats"]["championsKilled"]
                        champions_played[game["championId"]]["assists"] += game["stats"]["assists"]
                        champions_played[game["championId"]]["deaths"] += game["stats"]["numDeaths"]

                        if game["stats"]["win"]:
                            champions_played[game["championId"]]["wins"] += 1

                    except KeyError:
                        champions_played[game["championId"]] = {
                            "id": game["championId"],
                            "plays": 1,
                            "wins": 1 if game["stats"]["win"] else 0,
                            "kills": 0 if "championsKilled" not in game["stats"].keys() else game["stats"]["championsKilled"],
                            "assists": 0 if "numDeaths" not in game["stats"].keys() else game["stats"]["numDeaths"],
                            "deaths": 0 if "assists" not in game["stats"].keys() else game["stats"]["assists"],
                        }

            most_played = champions_played[max(champions_played, key=lambda x: champions_played[x]["plays"])]
            champion = api.static_get_champion(most_played["id"], champ_data="info")

            collated["recent"] = {
                "name": champion["name"],
                "plays": most_played["plays"],
                "wins": most_played["wins"],
                "kda": "{}/{}/{}".format(
                    most_played["kills"],
                    most_played["deaths"],
                    most_played["assists"],
                )
            }

            score = api.get_mastery_score(summoner_id, region)
            top_champion = api.get_top_champions(summoner_id, region, count=1)[0]
            champion = api.static_get_champion(top_champion["championId"], champ_data="info")

            collated["mastery"] = {
                "level": top_champion["championLevel"],
                "last_play": datetime.datetime.fromtimestamp(
                    int(top_champion["lastPlayTime"])/1000
                ).strftime("%d-%m-%Y %I:%M %p"),
                "score": top_champion["championPoints"],
                "total_mastery": score,
                "champion": champion["name"],
            }

        except riotwatcher.LoLException as e:
            return collated

        return collated

    async def _ranked_player_summary(self, collated, summoner_id, region):
        try:
            ranked = api.get_ranked_stats(summoner_id, region=region)

            # TODO: Combine all champion static data requests
            favourite_champion = max([x for x in ranked["champions"] if x["id"] != 0], key=lambda d: d["stats"]["totalSessionsPlayed"])
            favourite_champion_name = api.static_get_champion(favourite_champion["id"], champ_data="info")

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
            # TODO: Add favourite role to ranked stats
            # TODO: Create the collated object with its data more cleanly
            player_in_league = [x for x in league[str(summoner_id)][0]["entries"] if x["playerOrTeamId"] == str(summoner_id)][0]
            collated["ranked"]["league"] = league[str(summoner_id)][0]["tier"].title()
            collated["ranked"]["division"] = player_in_league["division"]
            collated["ranked"]["points"] = player_in_league["leaguePoints"]
            collated["ranked"]["wins"] = player_in_league["wins"]
            collated["ranked"]["losses"] = player_in_league["losses"]

            ranked_general = [x for x in ranked["champions"] if x["id"] == 0][0]["stats"]
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

            # TODO: Add promo series info
        except riotwatcher.LoLException as e:
            return collated

        return collated

    async def live_game(self, summoner_id, region):
        try:
            platform = riotwatcher.platforms[region.lower()]
        except KeyError:
            platform = None

        try:
            game = api.get_current_game(summoner_id, platform, region)
        except riotwatcher.LoLException as e:
            if e == riotwatcher.error_404:
                return None


        general_info = {}
        red_team = []
        red_team_bans = []
        blue_team = []
        blue_team_bans = []

        general_info["duration"] = time.strftime("%M:%S", time.gmtime(game["gameLength"]))
        general_info["mode"] = game["gameMode"].title()
        general_info["start_time"] = datetime.datetime.fromtimestamp(
            int(game["gameStartTime"])/1000
        ).strftime("%I:%M %p")

        for each in game["bannedChampions"]:
            if each["teamId"] == 100:
                blue_team_bans.append(CHAMPIONS[str(each["championId"])]["name"])
            else:
                red_team_bans.append(CHAMPIONS[str(each["championId"])]["name"])

        read_team_bans = ", ".join(red_team_bans).strip() if len(red_team_bans) > 0 else None
        blue_team_bans = ", ".join(blue_team_bans).strip() if len(blue_team_bans) > 0 else None

        for each in game["participants"]:
            player = "• {} ({})".format(each["summonerName"], CHAMPIONS["data"][str(each["championId"])]["name"])
            player += ("\n\t- Runes: " + self._get_live_runes(each))
            player += ("\n\t- Masteries: " + self._get_live_masteries(each))
            # player += self._get_champion_stats(each)

            if each["teamId"] == 100:
                blue_team.append(player)
            else:
                red_team.append(player)

        red_team = "\n".join(red_team).strip()
        blue_team = "\n".join(blue_team).strip()

        return {
            "general": general_info,
            "red_team": red_team,
            "red_team_bans": red_team_bans,
            "blue_team": blue_team,
            "blue_team_bans": blue_team_bans,
        }

    def _get_live_runes(self, player):
        if player is None:
            return ""

        runes = ""
        for each in player["runes"]:
            runes += "{}x{}".format(
                RUNES["data"][str(each["runeId"])]["name"],
                each["count"],
            )

            if player["runes"].index(each) != len(player["runes"]):
                runes += ", "
            else:
                runes += "\n"

        return runes

    def _get_live_masteries(self, player):
        if player is None:
            return ""

        masteries = "{}-{}-{}"
        ferocity_count = 0
        cunning_count = 0
        resolve_count = 0

        for each in player["masteries"]:
            t = self._get_mastery_tree(each["masteryId"])
            if t == 0:
                ferocity_count += each["rank"]
            elif t == 1:
                cunning_count += each["rank"]
            elif t == 2:
                resolve_count += each["rank"]

        return masteries.format(ferocity_count, cunning_count, resolve_count)

    def _get_mastery_tree(self, mastery_id):
        ferocity = []
        for each in MASTERIES["tree"]["Ferocity"]:
            ferocity.extend([x["masteryId"] for x in each["masteryTreeItems"] if x is not None])

        cunning = []
        for each in MASTERIES["tree"]["Cunning"]:
            cunning.extend([x["masteryId"] for x in each["masteryTreeItems"] if x is not None])

        resolve = []
        for each in MASTERIES["tree"]["Resolve"]:
            resolve.extend([x["masteryId"] for x in each["masteryTreeItems"] if x is not None])

        if mastery_id in ferocity:
            return 0
        elif mastery_id in cunning:
            return 1
        elif mastery_id in resolve:
            return 2
        else:
            return -1

class Responses:
    UPDATED_LOL_USERNAME = "{sender}\nUpdated your LoL username to {name} on region {region} 👍"

    STORED_LOL_USERNAME =  "{sender}\nStored your LoL name on {region} 👍"

    PLAYER_SUMMARY = (
        "```py\n"
        "Summoner name: {name}\n"
        "Summoner level: {level}\n"
        "Region: {region}\n"
        "Recently played: {recent[name]} ({recent[plays]} plays, {recent[wins]} win(s), {recent[kda]} KDA)\n"
        "Total champion mastery: {mastery[total_mastery]}\n"
        "Highest champion mastery: {mastery[champion]} (Level {mastery[level]}, {mastery[score]} score, last played {mastery[last_play]})\n"
        "Normal games won: {normal_wins}\n"
        "-------\n"
        "Ranked stats\n"
        "-------\n"
        "League: {ranked[league]} {ranked[division]}, {ranked[points]} points\n"
        "Games this season: {ranked[wins]} win(s), {ranked[losses]} losses\n"
        "Favourite champion: {ranked[fav][name]} ({ranked[fav][plays]} plays, {ranked[fav][wins]} win(s), {ranked[fav][kda]} K/D/A)\n"
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

    NOT_IN_GAME = "Summoner {name} is not in game on {region}"

    LIVE_GAME = (
        "```py\n"
        "Game type: {general[mode]}\n"
        "Game duration: {general[duration]}\n"
        "Game start time: {general[start_time]}\n"
        "--------------\n"
        "RED TEAM\n"
        "--------------\n"
        "Bans: {red_team_bans}\n"
        '{red_team}\n'
        "--------------\n"
        "BLUE TEAM\n"
        "--------------\n"
        "Bans: {blue_team_bans}\n"
        "{blue_team}\n"
        "```\n"
    )