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

    def get_dict(self):
        return self._data


class User(SlashBotDatabase):
    user_id = CharField(primary_key=True)
    user_name = TextField(index=True)
    join_date = DateTimeField(null=True)
    last_online = DateTimeField(null=True)


class Server(SlashBotDatabase):
    server_id = CharField(primary_key=True)
    server_name = TextField(index=True)
    owner = CharField(help_text="Server creator's ID")
    region = CharField()
    bot_add_date = DateTimeField(help_text="Date the bot was added to this server", null=True)
    currently_joined = BooleanField(help_text="Indicates whether the bot is currently part of the server")


class Channel(SlashBotDatabase):
    channel_id = CharField(primary_key=True)
    channel_name = TextField(index=True)
    channel_type = CharField()
    server = ForeignKeyField(Server, related_name="server")


class BotStats(SlashBotDatabase):
    run_time = DateField(primary_key=True)
    stats_str = TextField(null=False)


class RiotUser(SlashBotDatabase):
    summoner_id = CharField(null=True)
    summoner_name = CharField()
    region = CharField()
    summoner_level = IntegerField(null=True)
    user = ForeignKeyField(User, related_name="riotusers")
    date_registered = DateField(help_text="Date this username was registered with the bot")
    server_registered = ForeignKeyField(Server, related_name="registration_server")
    channel_registered = ForeignKeyField(Channel, related_name="channel_registered")
    last_update_data = TextField(null=True)
    last_updated = DateTimeField(null=True)

    class Meta:
        primary_key = CompositeKey("summoner_name", "region", "user")


class RiotStaticData(SlashBotDatabase):
    key = CharField(primary_key=True)
    value = TextField(null=False)
    updated = DateTimeField(null=False)


class ScheduledCommand(SlashBotDatabase):
    fire_time = DateTimeField(help_text="The time at which this command should fire")
    module = CharField(help_text="The module which the command is to be passed")
    subcommand = CharField(help_text="The command to invoke, as the entire method name. Ex: cmd_freechamps")
    sender = TextField(help_text="The value to be passed to the command's sender keyword arg")
    params = TextField(help_text="The values to be passed to the command's param keyword arg")
    invoker = ForeignKeyField(User, related_name="user_invoked")
    server = ForeignKeyField(Server, related_name="server_invoked")
    channel = ForeignKeyField(Channel, related_name="channel_invoked")
    schedule_time = DateTimeField(help_text="The time at which this command was scheduled")

    class Meta:
        primary_key = CompositeKey("schedule_time", "channel", "invoker")


db.create_tables([
    User,
    Server,
    Channel,
    BotStats,
    RiotUser,
    RiotStaticData,
    ScheduledCommand,
], safe=True)

logging.debug("Created tables")
