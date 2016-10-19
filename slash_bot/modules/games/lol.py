# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import json
import riotwatcher
import datetime
import time
import re

from collections import Counter

import config

from errors import *
from models import *
from commands import *
from utils import *

BOT = config.GLOBAL["bot"]

api = None

_API_KEY = None

logger = logging.getLogger(__name__)

REGIONS = {
    "NA": riotwatcher.NORTH_AMERICA,
    "EUW": riotwatcher.EUROPE_WEST,
    "EUNE": riotwatcher.EUROPE_NORDIC_EAST,
    "JP": riotwatcher.JAPAN,
    "RU": riotwatcher.RUSSIA,
    "KR": riotwatcher.KOREA,
    "LAS": riotwatcher.LATIN_AMERICA_SOUTH,
    "LAN": riotwatcher.LATIN_AMERICA_NORTH,
    "TK": riotwatcher.TURKEY,
    "BR": riotwatcher.BRAZIL,
    "OCE": riotwatcher.OCEANIA,
}

REGION_NAMES = {
    riotwatcher.NORTH_AMERICA: "North America",
    riotwatcher.EUROPE_WEST: "EU West",
    riotwatcher.EUROPE_NORDIC_EAST: "EU Nordic and East",
    riotwatcher.JAPAN: "Japan",
    riotwatcher.KOREA: "Korea",
    riotwatcher.LATIN_AMERICA_NORTH: "Latin America North",
    riotwatcher.LATIN_AMERICA_SOUTH: "Latin America South",
    riotwatcher.TURKEY: "Turkey",
    riotwatcher.BRAZIL: "Brazil",
    riotwatcher.OCEANIA: "Oceania",
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
    "NORMAL": "Unranked on Summoner's Rift",
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

STAT_ATTRIBUTES = {
    "FlatSpellBlockMod": "Magic resist",
    "PercentMPRegenMod": "Mana regen %",
    "rFlatSpellBlockModPerLevel": "Magic resist per level",
    "rFlatArmorModPerLevel": "Armor per level",
    "PercentPhysicalDamageMod": "Phsyical damage %",
    "FlatCritChanceMod": "Critical strike chance",
    "PercentSpellBlockMod": "Magic resist %",
    "rFlatTimeDeadModPerLevel": "Reduce death time per level",
    "rFlatMagicDamageModPerLevel": "Ability power per level",
    "rFlatHPModPerLevel": "HP per level",
    "rPercentMovementSpeedModPerLevel": "Movement speed per level",
    "FlatEXPBonus": "XP bonus",
    "FlatMPRegenMod": "Mana regen",
    "rFlatHPRegenModPerLevel": "HP regen per level",
    "FlatBlockMod": "Reduce damage",
    "PercentEXPBonus": "XP bonus %",
    "FlatEnergyPoolMod": "Energy",
    "rFlatEnergyRegenModPerLevel": "Energy regen per level",
    "rFlatGoldPer10Mod": "Gold per 10",
    "FlatAttackSpeedMod": "Attack speed",
    "FlatHPPoolMod": "HP",
    "PercentAttackSpeedMod": "Attack speed %",
    "rFlatDodgeMod": "Dodge chance",
    "rFlatMPRegenModPerLevel": "Mana regen per level",
    "rPercentTimeDeadMod": "Reduce death timer %",
    "FlatEnergyRegenMod": "Energy regen",
    "PercentSpellVampMod": "Spell vamp %",
    "FlatCritDamageMod": "Critical damage",
    "rFlatMovementSpeedModPerLevel": "Movement speed per level",
    "PercentHPRegenMod": "HP regen %",
    "rPercentArmorPenetrationModPerLevel": "Armor penetration per level",
    "PercentArmorMod": "Armor %",
    "rFlatMPModPerLevel": "Mana per level",
    "rFlatArmorPenetrationMod": "Armor penetration",
    "PercentBlockMod": "Reduce damage %",
    "PercentMagicDamageMod": "Ability power %",
    "FlatMPPoolMod": "Mana",
    "FlatPhysicalDamageMod": "Physical damage",
    "rFlatPhysicalDamageModPerLevel": "Phsyical damage per level",
    "rFlatTimeDeadMod": "Reduce death time",
    "FlatHPRegenMod": "HP regen",
    "rFlatCritDamageModPerLevel": "Critical damage per level",
    "rFlatCritChanceModPerLevel": "Critical chance per level",
    "rFlatDodgeModPerLevel": "Dodge chance per level",
    "rPercentMagicPenetrationModPerLevel": "Magic penetration per level",
    "PercentLifeStealMod": "Life steal %",
    "PercentMovementSpeedMod": "Movement speed %",
    "FlatArmorMod": "Armor",
    "rFlatEnergyModPerLevel": "Energy per level",
    "rPercentMagicPenetrationMod": "Magic penetration",
    "rPercentTimeDeadModPerLevel": "Reduce death time per level %",
    "PercentMPPoolMod": "Mana %",
    "PercentDodgeMod": "Dodge chance %",
    "PercentCritChanceMod": "Critical strike chance %",
    "PercentCritDamageMod": "Critical strike damage %",
    "rPercentAttackSpeedModPerLevel": "Attack speed per level %",
    "rFlatMagicPenetrationMod": "Magic penetration",
    "PercentHPPoolMod": "HP",
    "rPercentArmorPenetrationMod": "Armor penetration %",
    "rFlatMagicPenetrationModPerLevel": "Magic penetration per level",
    "rFlatArmorPenetrationModPerLevel": "Armor penetration per level",
    "rPercentCooldownModPerLevel": "Cooldown reduction per level",
    "FlatMagicDamageMod": "Magic damage",
    "FlatMovementSpeedMod": "Movement speed",
    "rPercentCooldownMod": "Cooldown reduction %",
}

# Static data
CHAMPIONS = None
MASTERIES = None
RUNES = None
SUMMONER_SPELLS = None

CONFIG = config.MODULES["League of Legends"]["config"]

if _API_KEY is None:
    with open(config.PATHS["rito_creds"], "r") as cf_r:
        _API_KEY = json.load(cf_r)["api_key"]

if api is None:
    api = riotwatcher.RiotWatcher(_API_KEY)


def riot_api_error():
    logger.error("Non 404/204 error with riot API")
    return ThirdPartyAPIError("Error communicating with the Riot Games API")


def refresh_static_data(key="ALL"):
    """Refreshes all static LoL data

    Retrieves static data for champions, masteries, runes and summoner spells and assigns them to their
    respective global variables if they haven't been initialised yet or `key` includes them.

    Args:
        key (str): Valid values are the names of any of the static variables or "ALL"

    """
    global CHAMPIONS
    global MASTERIES
    global RUNES
    global SUMMONER_SPELLS

    if CHAMPIONS is None or key in ["CHAMPIONS", "ALL"]:
        CHAMPIONS = api.static_get_champion_list(region=riotwatcher.NORTH_AMERICA, data_by_id=True, champ_data="all")
        logger.debug("Collected {} champions".format(len(CHAMPIONS["data"])))

    if MASTERIES is None or key in ["MASTERIES", "ALL"]:
        MASTERIES = api.static_get_mastery_list(region=riotwatcher.NORTH_AMERICA, mastery_list_data="all")
        logger.debug("Collected {} masteries".format(len(MASTERIES["data"])))

    if RUNES is None or key in ["RUNES", "ALL"]:
        RUNES = api.static_get_rune_list(region=riotwatcher.NORTH_AMERICA, rune_list_data="all")
        logger.debug("Collected {} runes".format(len(RUNES["data"])))

    if SUMMONER_SPELLS is None or key in ["SUMMONER_SPELLS", "ALL"]:
        SUMMONER_SPELLS = api.static_get_summoner_spell_list(region=riotwatcher.NORTH_AMERICA, spell_data="all")
        logger.debug("Collected {} summoner spells".format(len(SUMMONER_SPELLS["data"])))


def refresh_champion_assets(champion_name=None):
    """Refreshes champion icons

    If `champion_name` is not given, the method loads any missing icons.

    Args:
        champion_name (str): If given, reloads icon regardless of whether it already exists

    Raises:
        ValueError: If champion name is given and it is not a valid champion

    """
    if champion_name is not None:
        if champion_name not in [x[name] for x in CHAMPIONS["data"]]:
            raise ValueError("{} is not a valid champion".format(champion_name))
        AssetStore.store(api.get_champion_icon(champion_name=champion_name))

    for id_, data in CHAMPIONS["data"].items():
        try:
            AssetStore.get("lol/icons/champions/{}".format(id_))
        except AssetsError:
            AssetStore.store(api.get_champion_icon(champion_name=data["image"]["full"]))

current_time = datetime.datetime.now()
logger.debug("Collecting static data")
try:
    CHAMPIONS = RiotStaticData.get(key="CHAMPIONS")
    if int((current_time - CHAMPIONS.updated).total_seconds()) >= int(CONFIG["static_refresh_interval"]["value"]):
        refresh_static_data(key="CHAMPIONS")
        RiotStaticData.update(
            value=json.dumps(CHAMPIONS),
            updated=datetime.datetime.now()
        ).where(RiotStaticData.key == "CHAMPIONS").execute()
    else:
        logger.debug("Champions already exist")
        CHAMPIONS = json.loads(CHAMPIONS.value)

    MASTERIES = RiotStaticData.get(key="MASTERIES")
    if int((current_time - MASTERIES.updated).total_seconds()) >= int(CONFIG["static_refresh_interval"]["value"]):
        refresh_static_data(key="MASTERIES")
        RiotStaticData.update(
            value=json.dumps(MASTERIES),
            updated=datetime.datetime.now()
        ).where(RiotStaticData.key == "MASTERIES").execute()
    else:
        logger.debug("Masteries already exist")
        MASTERIES = json.loads(MASTERIES.value)

    RUNES = RiotStaticData.get(key="RUNES")
    if int((current_time - RUNES.updated).total_seconds()) >= int(CONFIG["static_refresh_interval"]["value"]):
        refresh_static_data(key="RUNES")
        RiotStaticData.update(
            value=json.dumps(RUNES),
            updated=datetime.datetime.now()
        ).where(RiotStaticData.key == "RUNES").execute()
    else:
        logger.debug("Runes already exist")
        RUNES = json.loads(RUNES.value)

    SUMMONER_SPELLS = RiotStaticData.get(key="SUMMONER_SPELLS")
    if int((current_time - SUMMONER_SPELLS.updated).total_seconds()) >= int(CONFIG["static_refresh_interval"]["value"]):
        refresh_static_data(key="SUMMONER_SPELLS")
        RiotStaticData.update(
            value=json.dumps(SUMMONER_SPELLS),
            updated=datetime.datetime.now()
        ).where(RiotStaticData.key == "SUMMONER_SPELLS").execute()
    else:
        logger.debug("Summoner spells already exist")
        SUMMONER_SPELLS = json.loads(SUMMONER_SPELLS.value)

except RiotStaticData.DoesNotExist:
    logger.debug("One or more static data keys are missing, refreshing all")
    refresh_static_data()
    timestamp = datetime.datetime.now()

    static_data = [
        {"key": "CHAMPIONS", "value": json.dumps(CHAMPIONS), "updated": timestamp},
        {"key": "MASTERIES", "value": json.dumps(MASTERIES), "updated": timestamp},
        {"key": "RUNES", "value": json.dumps(RUNES), "updated": timestamp},
        {"key": "SUMMONER_SPELLS", "value": json.dumps(SUMMONER_SPELLS), "updated": timestamp},
    ]
    # TODO: Change to upsert
    RiotStaticData.insert_many(static_data).execute()


class LeagueOfLegendsCommand(Command):
    command = "lol"

    def __init__(self, message):
        super().__init__(message)

        self.subcommands_map = {}
        for cmd in LeagueOfLegendsFunctions.__dict__.values():
            if isinstance(cmd, type) and issubclass(cmd, LeagueOfLegendsCommand):
                if len(cmd.command) > 0:
                    self.subcommands_map[cmd.command] = cmd
                    if len(cmd.aliases) > 0:
                        for each in cmd.aliases:
                            self.subcommands_map[each] = cmd

    def get_delegate_command(self):
        if len(self.params) > 0 and self.params[0] in self.subcommands_map.keys():
            return self.subcommands_map[self.params[0]](self._raw_message)

    @classmethod
    async def create_command(cls, message):
        return LeagueOfLegendsCommand(message).get_delegate_command()


class LeagueOfLegendsFunctions(object):
    class SetName(LeagueOfLegendsCommand):
        command = "setname"
        aliases = ["setn", ]

        @overrides(Command)
        async def make_response(self):
            try:
                summoner, region = parse_username_region(self.params[1:])
            except SlashBotValueError as e:
                raise SlashBotValueError(str(e), mention=self.invoker.mention)

            user = User.get_or_create(user_id=self.invoker.id, defaults={
                "user_id": self.invoker.id,
                "user_name": self.invoker.name,
            })[0]

            new_data = {
                "summoner_name": summoner,
                "region": region,
                "user": user.user_id,
                "date_registered": datetime.datetime.now(),
                "server_registered": self.invoker.server.id,
                "channel_registered": self.source_channel.id,
                "last_update_data": None,
                "last_updated": None,
            }

            riotuser, created = RiotUser.get_or_create(defaults=new_data, user=self.invoker.id, region=region)

            if not created:
                for field, value in new_data.items():
                    if field == "user":
                        continue

                    setattr(riotuser, field, value)

                riotuser.save()
                self.response = "{sender}\nUpdated your LoL username to {name} on region {region} 👍".format(
                    sender=self.invoker.mention,
                    name=summoner,
                    region=REGION_NAMES[region]
                )
            else:
                self.response = "{sender}\nStored your LoL name on {region} 👍".format(
                    sender=self.invoker.mention,
                    region=REGION_NAMES[region]
                )

    class SummonerInfo(LeagueOfLegendsCommand):
        command = "summoner"
        aliases = ["sumn", "player", ]

        @overrides(Command)
        async def make_response(self):
            local_summoner = get_summoner_info(self.invoker, self.params[1:])

            if local_summoner["last_updated"] is not None and (
                datetime.datetime.now() - local_summoner["last_updated"]
            ).total_seconds() / 60 < 5:
                return json.loads(local_summoner["last_update_data"])

            summoner = api.get_summoner(_id=local_summoner["id"], region=local_summoner["region"])

            try:
                stats = api.get_stat_summary(local_summoner["id"], region=local_summoner["region"])

                unranked_stats = [stat_summary for stat_summary in stats["playerStatSummaries"]
                                  if stat_summary["playerStatSummaryType"] == "Unranked"][0]

            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    raise SlashBotValueError("This summoner doesn't seem to have played any games!", mention=self.invoker.mention)

            champions_played = {}
            try:
                recent_games = api.get_recent_games(local_summoner["id"], region=local_summoner["region"])
            except riotwacher.LoLException as e:
                if e == riotwatcher.error_404:
                    recent_games = []
                    champions_played = {
                        "id": "-",
                        "plays": "-",
                        "wins": "-",
                        "kills": "-",
                        "assists": "-",
                        "deaths": "-",
                    }
                else:
                    riot_api_error()

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

            if len(champions_played) > 0:
                most_played = champions_played[max(champions_played, key=lambda x: champions_played[x]["plays"])]
            else:
                most_played = {
                    "id": None,
                    "plays": "-",
                    "wins": "-",
                    "kills": "-",
                    "deaths": "-",
                    "assists": "-",
                }

            general_info = (
                "Summoner name: {name}\n"
                "Summoner level: {level}\n"
                "Region: {region}\n"
                "Recently played: {recent[name]} ({recent[plays]} plays, {recent[wins]} win(s), {recent[kda]} KDA)\n"
                "Normal games won: {normal_wins}"
            ).format(
                name=summoner["name"],
                level=summoner["summonerLevel"],
                region=REGION_NAMES[local_summoner["region"]],
                recent={
                    "name": CHAMPIONS["data"][str(most_played["id"])]["name"] if most_played["id"] is not None else "-",
                    "plays": most_played["plays"],
                    "wins": most_played["wins"],
                    "kda": "{}/{}/{}".format(
                        most_played["kills"],
                        most_played["deaths"],
                        most_played["assists"],
                    ),
                },
                normal_wins=unranked_stats["wins"],
            )

            try:
                score = api.get_mastery_score(local_summoner["id"], local_summoner["region"])
            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_204:
                    score = None
            try:
                top_champion = api.get_top_champions(local_summoner["id"], local_summoner["region"], count=1)
                if len(top_champion) > 0:
                    top_champion = top_champion[0]
                else:
                    top_champion = None
            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    top_champion = None
                else:
                    riot_api_error()

            mastery_info = (
                "Total champion mastery: {total_mastery}\n"
                "Highest champion mastery: {champion} (Level {level}, {score} score, last played {last_play})"
            ).format(
                total_mastery=score if score else 0,
                champion=CHAMPIONS["data"][str(top_champion["championId"])]["name"] if top_champion else None,
                level=top_champion["championLevel"] if top_champion else "-",
                last_play=datetime.datetime.fromtimestamp(
                    int(top_champion["lastPlayTime"]) / 1000
                ).strftime("%d-%m-%Y %I:%M %p") if top_champion else "-",
                score=top_champion["championPoints"] if top_champion else "-",
            )

            try:
                ranked_stats = api.get_ranked_stats(local_summoner["id"], region=local_summoner["region"])
                favourite_champion = max([x for x in ranked_stats["champions"] if x["id"] != 0],
                                         key=lambda d: d["stats"]["totalSessionsPlayed"])
                league = api.get_league(summoner_ids=[local_summoner["id"], ], region=local_summoner["region"])
                player_in_league = [x for x in league[str(local_summoner["id"])][0]["entries"] if
                                    x["playerOrTeamId"] == str(local_summoner["id"])][0]
                ranked_general = [x for x in ranked_stats["champions"] if x["id"] == 0][0]["stats"]

                ranked_info = (
                    "League: {league} {division}, {points} points\n"
                    "Games this season: {wins} win(s), {losses} losses\n"
                    "Favourite champion: {fav[name]} ({fav[plays]} plays, {fav[wins]} win(s), {fav[kda]} K/D/A)\n"
                    # "Favourite position: {role}\n"
                    "Average K/D/A: {kills_avg}/{deaths_avg}/{assists_avg}\n"
                    "Total K/D/A: {kills}/{deaths}/{assists}\n"
                    "Largest killing spree: {largest_spree}\n"
                    "Double/Triple/Quadra/Penta: {double}/{triple}/{quadra}/{penta}\n"
                    "Creep score: {cs}\n"
                    "Gold earned: {gold}\n"
                    "Towers destroyed: {towers}"
                    # "MMR: {mmr}"
                ).format(
                    fav={
                        "name": CHAMPIONS["data"][str(favourite_champion["id"])]["name"],
                        "plays": favourite_champion["stats"]["totalSessionsPlayed"],
                        "wins": favourite_champion["stats"]["totalSessionsWon"],
                        "kda": "{}/{}/{}".format(
                            favourite_champion["stats"]["totalChampionKills"],
                            favourite_champion["stats"]["totalDeathsPerSession"],
                            favourite_champion["stats"]["totalAssists"]
                        )
                    },
                    league=league[str(local_summoner["id"])][0]["tier"].title(),
                    division=player_in_league["division"],
                    points=player_in_league["leaguePoints"],
                    wins=player_in_league["wins"],
                    losses=player_in_league["losses"],
                    kills_avg=round(ranked_general["totalChampionKills"] / ranked_general["totalSessionsPlayed"], 2),
                    deaths_avg=round(ranked_general["totalDeathsPerSession"] / ranked_general["totalSessionsPlayed"], 2),
                    assists_avg=round(ranked_general["totalAssists"] / ranked_general["totalSessionsPlayed"], 2),
                    kills=ranked_general["totalChampionKills"],
                    deaths=ranked_general["totalDeathsPerSession"],
                    assists=ranked_general["totalAssists"],
                    largest_spree=ranked_general["maxLargestKillingSpree"],
                    double=ranked_general["totalDoubleKills"],
                    triple=ranked_general["totalTripleKills"],
                    quadra=ranked_general["totalQuadraKills"],
                    penta=ranked_general["totalPentaKills"],
                    cs=ranked_general["totalMinionKills"],
                    gold=ranked_general["totalGoldEarned"],
                    towers=ranked_general["totalTurretsKilled"],
                )
            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    ranked_info = "No ranked stats for this player"
                else:
                    riot_api_error()

            summary = "```py\n{}\n{}\n----------------------\nRanked Stats\n----------------------\n{}\n```".format(
                general_info,
                mastery_info,
                ranked_info,
            )

            r = RiotUser.update(last_update_data=json.dumps(summary), last_updated=datetime.datetime.now()).where(
                (RiotUser.summoner_id == local_summoner["id"]) & (RiotUser.region == local_summoner["region"])
            ).execute()

            if r < 1:
                logger.error("There was an error updating player info for summoner {} {}".format(
                    local_summoner["id"],
                    local_summoner["region"]
                ))

            self.response = summary

    class LiveGame(LeagueOfLegendsCommand):
        command = "game"
        aliases = ["g", "live", ]

        @overrides(Command)
        async def make_response(self):
            summoner = get_summoner_info(self.invoker, self.params[1:])

            try:
                platform = riotwatcher.platforms[summoner["region"]]
            except KeyError:
                platform = None

            try:
                game = api.get_current_game(summoner["id"], platform, summoner["region"])

                red_team = []
                red_team_bans = []
                blue_team = []
                blue_team_bans = []

                for each in game["bannedChampions"]:
                    if each["teamId"] == 100:
                        blue_team_bans.append(CHAMPIONS["data"][str(each["championId"])]["name"])
                    else:
                        red_team_bans.append(CHAMPIONS["data"][str(each["championId"])]["name"])

                for each in game["participants"]:
                    player = "• {} ({})".format(each["summonerName"], CHAMPIONS["data"][str(each["championId"])]["name"])
                    player += ("\n\t- Champion mastery: Level: {level}, score: {score}".format(
                        **get_player_champion(each, summoner["region"]))
                    )
                    player += ("\n\t- Masteries: {ferocity}-{cunning}-{resolve}".format(**get_masteries(each["masteries"])))
                    player += ("\n\t- Runes: " + get_player_runes(each))

                    if each["teamId"] == 100:
                        blue_team.append(player)
                    else:
                        red_team.append(player)

                summary = (
                    "Game type: {mode}\n"
                    "Game duration: {duration}\n"
                    "Game start time: {start_time}\n"
                    "#$$#"
                    "--------------\n"
                    "RED TEAM\n"
                    "--------------\n"
                    "Bans: {red_team_bans}\n"
                    '{red_team}\n'
                    "#$$#"
                    "--------------\n"
                    "BLUE TEAM\n"
                    "--------------\n"
                    "Bans: {blue_team_bans}\n"
                    "{blue_team}"
                ).format(
                    mode=game["gameMode"].title(),
                    duration=time.strftime("%M:%S", time.gmtime(game["gameLength"])),
                    start_time=datetime.datetime.fromtimestamp(
                        int(game["gameStartTime"]) / 1000
                    ).strftime("%I:%M %p"),
                    red_team_bans=", ".join(red_team_bans).strip() if len(red_team_bans) > 0 else None,
                    blue_team_bans=", ".join(blue_team_bans).strip() if len(blue_team_bans) > 0 else None,
                    red_team="\n".join(red_team).strip(),
                    blue_team="\n".join(blue_team).strip(),
                )

                self.response = summary

            except riotwatcher.LoLException as e:
                if e == riotwatcher.error_404:
                    return "{sender}\nSummoner {name} is not in game on {region}".format(
                        sender=self.invoker.mention,
                        name=summoner["name"],
                        region=REGION_NAMES[summoner["region"]]
                    )
                else:
                    riot_api_error()

    class PlayerRunePages(LeagueOfLegendsCommand):
        command = "runes"
        aliases = ["r", "runepages", ]

        @overrides(Command)
        async def make_response(self):
            summoner = get_summoner_info(self.invoker, self.params[1:])

            try:
                rune_pages = api.get_rune_pages([summoner["id"], ], region=summoner["region"])
            except riotwatcher.LoLException:
                raise SlashBotValueError("Error getting rune pages for this summoner", mention=self.invoker.mention)

            rune_page_data = {}
            for page in rune_pages[summoner["id"]]["pages"]:
                rune_page_data[page["name"]] = {
                    "page": get_player_rune_page(page),
                    "stats": get_rune_page_stats(page),
                }

            runes_summary = ""
            idx = 1
            for name, page in rune_page_data.items():
                runes_summary += "• {}".format(name)

                for rune in page["page"]:
                    runes_summary += "\n\t♦ {} x {}".format(rune["count"], rune["name"])

                runes_summary += "\n\n\tStats:"
                for name, value in page["stats"].items():
                    runes_summary += "\n\t♦ {}: {}".format(name, value)

                idx += 1
                if idx <= len(rune_page_data):
                    runes_summary += "\n"

            self.response = "```py\n{}\n```".format(runes_summary)

    class PlayerMasteryPages(LeagueOfLegendsCommand):
        command = "mastery"
        aliases = ["m", "masterypages", ]

        @overrides(Command)
        async def make_response(self):
            summoner = get_summoner_info(self.invoker, self.params[1:])

            try:
                mastery_pages = api.get_mastery_pages([summoner["id"], ], region=summoner["region"])
            except riotwatcher.LoLException:
                raise SlashBotValueError("Error getting mastery pages for this summoner", mention=self.invoker.mention)

            masteries_summary = "Summoner level: {}\n".format(summoner["level"])
            idx = 1
            for page in mastery_pages[summoner["id"]]["pages"]:
                try:
                    masteries_summary += "• {page}: {ferocity}-{cunning}-{resolve}".format(
                        page=page["name"],
                        **get_masteries(page["masteries"]),
                    )
                except KeyError:
                    masteries_summary += "• {page}: 0-0-0".format(page=page["name"])

                idx += 1
                if idx <= len(mastery_pages[summoner["id"]]["pages"]):
                    masteries_summary += "\n"

            self.response = "```py\n{}\n```".format(masteries_summary)

    class FreeChampionRotation(LeagueOfLegendsCommand):
        command = "freechamps"
        aliases = ["fc", ]

        @overrides(Command)
        async def make_response(self):
            region = "NA"
            if len(self.params) > 1:
                region = self.params[1]
                if region not in REGIONS.keys():
                    raise SlashBotValueError("Unknown region {}".format(region), mention=self.invoker.mention)

            free_champions = api.get_all_champions(region=REGIONS[region], free_to_play=True)["champions"]
            free_champions = [
                "• {name}, {title}".format(
                    name=CHAMPIONS["data"][str(x["id"])]["name"],
                    title=CHAMPIONS["data"][str(x["id"])]["title"],
                ) for x in free_champions
            ]

            free_champions_summary = "\n".join(free_champions)
            free_champions_summary = "Free champions for {region}:\n```py\n{champions}\n```".format(
                region=REGION_NAMES[region.lower()],
                champions=free_champions_summary
            )

            self.response = free_champions_summary


def get_summoner_info(discord_user, params):
    if len(params) <= 1:
        if len(params) == 0:
            uid = discord_user.id
            try:
                riotuser = RiotUser.get(user=uid)
                summoner = {
                    "name": riotuser.summoner_name,
                    "id": riotuser.summoner_id,
                    "region": riotuser.region,
                    "level": riotuser.summoner_level,
                    "last_updated": riotuser.last_updated,
                    "last_update_data": riotuser.last_update_data,
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
                    "level": riotuser.summoner_level,
                    "last_updated": riotuser.last_updated,
                    "last_update_data": riotuser.last_update_data,
                }
            except RiotUser.DoesNotExist:
                raise SlashBotValueError(
                    "{} no summoner names have been stored for this user."
                    " They must `,lol setname` first.".format(discord_user.mention)
                )

        else:
            raise CommandFormatError("You didn't give me enough details. Expected `<user/summoner name> <region>`")

    else:
        name, region = parse_username_region(params)
        summoner = {
            "name": name,
            "id": None,
            "region": region,
            "level": None,
            "last_updated": None,
            "last_update_data": None,
        }

    return update_summoner_info(summoner)


def update_summoner_info(summoner):
    if summoner["id"] is None:
        try:
            rito_resp = api.get_summoner(summoner["name"], region=summoner["region"])
        except riotwatcher.LoLException as e:
            if e == riotwatcher.error_404:
                raise SlashBotValueError("Summoner {} not found on region {}".format(summoner["name"], summoner["region"]))

        summoner["id"] = str(rito_resp["id"])
        summoner["level"] = int(rito_resp["summonerLevel"])

        r = RiotUser.update(
            summoner_id=rito_resp["id"],
            summoner_level=rito_resp["summonerLevel"]
        ).where(

            (RiotUser.summoner_name == summoner["name"]) & (RiotUser.region == summoner["region"])
        ).execute()

        if r < 1:
            logger.debug(
                ("Local player info/summoner id wasn't updated for summoner {} on {}."
                    "Either this user isn't stored locally or there was an error updating.").format(
                        summoner["name"],
                        summoner["region"]
                )
            )

    return summoner


def parse_username_region(params):
    try:
        if len(params) == 2:
            return (params[0], REGIONS[params[1]])
        else:
            region = REGIONS[params[-1].upper()]
            params = params[:-1]
            name = " ".join(params)
    except KeyError:
        raise SlashBotValueError("Unknown region")

    return (name, region)


def get_player_runes(player):
    if player is None:
        return ""

    runes = ""
    for each in player["runes"]:
        runes += "\n\t\t♦ {count} x {rune}".format(
            count=each["count"],
            rune=RUNES["data"][str(each["runeId"])]["name"],
        )

    return runes


def get_player_rune_page(page):
    runes = []
    runes_raw = Counter([x["runeId"] for x in page["slots"]])
    for each in runes_raw:
        runes.append({
            "name": RUNES["data"][str(each)]["name"],
            "count": runes_raw[each],
        })

    return runes


def get_rune_page_stats(page):
    stats = {}
    runes_raw = Counter([x["runeId"] for x in page["slots"]])
    for rune, count in runes_raw.items():
        rune = RUNES["data"][str(rune)]
        for key, value in rune["stats"].items():
            stats[STAT_ATTRIBUTES[key]] = round(value * count, 2)

    return stats


def get_masteries(page):
    masteries = {
        "ferocity": 0,
        "cunning": 0,
        "resolve": 0,
    }
    id_key = "id"
    # Masteries enpoint uses "id" & currentgame uses "masteryId"
    try:
        if page[0][id_key]:
            pass
    except KeyError:
        id_key = "masteryId"

    for mastery in page:
        t = get_mastery_tree(mastery[id_key])
        if t == 0:
            masteries["ferocity"] += mastery["rank"]
        elif t == 1:
            masteries["cunning"] += mastery["rank"]
        elif t == 2:
            masteries["resolve"] += mastery["rank"]

    return masteries


def get_mastery_tree(mastery_id):
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


def get_player_champion(player, region):
    if not player:
        return ""

    mastery = None
    try:
        mastery = api.get_champion_mastery(
            summoner_id=player["summonerId"],
            champion_id=player["championId"],
            region=region
        )
    except riotwatcher.LoLException as e:
        if e == riotwatcher.error_204:
            return {"level": 0, "score": 0}
        if e == riotwatcher.error_429:
            return get_player_champion(player, region)

    return {"level": mastery["championLevel"], "score": mastery["championPoints"]}
