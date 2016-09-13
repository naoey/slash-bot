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

db.create_tables([
    User,
    Server,
    Channel,
    RiotUser,
    BotStats,
], safe=True)

logging.debug("Created tables")
