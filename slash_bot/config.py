# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

VERSION = "0.0.3"

BOT_PREFIX = ","

PATHS = {
    "logs_dir": "./../logs/",

    "database": "./../slash_bot.db",

    "discord_creds": "./../private/discord.json",
    "rito_creds": "./../private/rito.json",
}

MODULES = {
    "League of Legends": {
        "location": "games.lol",
        "class": "LeagueOfLegends",
        "active": True,
        "prefix": "lol",
    },
    "osu!": {
        "location": "games.osu.Osu",
        "class": "Osu",
        "active": False,
        "prefix": "osu",
    },
    "MyAnimeList": {
        "location": "anime.mal.MyAnimeList",
        "class": "MyAnimeList",
        "active": False,
        "prefix": "mal",
    },
}

API_LIMITS = {
    "riot": {
        "10": "10",
        "600": "500",
    }
}

GLOBAL = {

}

DISCORD_STATUS_ITER = [
    "procrastination \(^-^)/",
]
