# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

VERSION = "0.3.2"

BOT_PREFIX = ","

PATHS = {
    "logs_dir": "./../logs/",

    "database": "./../slash_bot.db",

    "discord_creds": "./../private/discord.json",
    "rito_creds": "./../private/rito.json",
    "osu_creds": "./../private/osu.json",

    "assets": "./../assets/",
}

URIS = {
    "github": "https://github.com/naoey/slash-bot",
}

MODULES = {
    "Administration": {
        "location": "administration",
        "active": False,
        "config": {},
    },
    "Management": {
        "location": "management",
        "active": True,
        "config": {},
    },
    "League of Legends": {
        "location": "games.lol",
        "class": "LeagueOfLegends",
        "active": True,
        "prefix": "lol",
        "config": {
            "static_refresh_interval": {
                "value": 604800,
                "description": "The time interval in seconds before refreshing static data"
            },
            "player_data_refresh_interval": {
                "value": 1200,
                "description": "The time interval in seconds before hitting rito APIs again for player data instead of using stored cache"
            }
        }
    },
    "osu!": {
        "location": "games.osu",
        "class": "Osu",
        "active": True,
        "prefix": "osu",
        "config": {},
    },
    "MyAnimeList": {
        "location": "anime.mal.MyAnimeList",
        "class": "MyAnimeList",
        "active": False,
        "prefix": "mal",
        "config": {},
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

STATUS_CHANGE_INTERVAL = 60
DISCORD_STATUS_ITER = [
    "procrastination \(^-^)/",
]
