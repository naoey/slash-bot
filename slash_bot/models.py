# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import config

from peewee import *

db = SqliteDatabase(config.PATHS["database"])
db.connect()

logging.debug("Connected to database")

class SlashBotDatabase(Model):
    class Meta:
        database = db

class User(SlashBotDatabase):
    user_id = CharField(primary_key=True)
    user_name = TextField(index=True)
    join_date = DateTimeField(null=True)
    last_online = DateTimeField(null=True)

class Server(SlashBotDatabase):
    server_id = CharField(primary_key=True)
    server_name = TextField(index=True)
    bot_add_date = DateTimeField(help_text="Date the bot was added to this server")

class Channel(SlashBotDatabase):
    channel_id = CharField(primary_key=True)
    channel_name = TextField(index=True)
    channel_top = TextField(null=True)

class BotStats(SlashBotDatabase):
    run_time = DateField(primary_key=True)
    stats_str = TextField(null=False)

class RiotUser(SlashBotDatabase):
    summoner_id = CharField(null=True)
    summoner_name = CharField()
    region = CharField()
    user = ForeignKeyField(User, related_name="riotusers")
    date_registered = DateField(help_text="Date this username was registered with the bot")
    server_registered = ForeignKeyField(Server, related_name="registration_server")
    channel_registered = ForeignKeyField(Channel, related_name="channel_registered")
    last_update_data = TextField(null=True)
    last_updated = DateTimeField(null=True)

class Meta:
    primary_key = CompositeKey("summoner_name", "region", "user")

db.create_tables([
    User,
    Server,
    Channel,
    BotStats,
], safe=True)

logging.debug("Created tables")
