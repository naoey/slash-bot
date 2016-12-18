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
    "credentials_file": "./../private/credentials.json",
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
    "Utilities": {
        "location": "utilities",
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
                "description": "The time interval in seconds before refreshing static data",
            },
            "player_data_refresh_interval": {
                "value": 1200,
                "description": "The time interval in seconds before hitting rito APIs again for player data instead of using stored cache",
            },
        },
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
    "Music": {
        "location": "music.music",
        "active": True,
        "config": {
            "max_queue_size": {
                "value": 250,
                "description": "The maximum number of songs that can be queued after which queue requests are ignored",
            },
            "max_active_players": {
                "value": 15,
                "description": "The maximum number of active music players after which new players will remain paused until an existing player stops",
            },
            "own_server_only": {
                "value": False,
                "description": "Defines if music can be played only on the bot's server",
            },
        },
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
