# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import logging.config  # find out why this is necessary when logging already imported
import discord
import time
import datetime
import os
import sys
import json
import importlib
import threading

from functools import partial

import config
import errors

from utils import *
from models import Server, Channel, BotStats
from commands import *

LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "debug": {
            "format": "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
        },
        "error": {
            "format": "%(levelname)s at %(asctime)s in %(funcName)s in %(filename) at line %(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "debug",
            "level": logging.DEBUG
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "error",
            "level": logging.ERROR,
            "filename": os.path.join(config.PATHS["logs_dir"], "slash_bot_{}.log".format(str(int(time.time()))))
        },
        # "discord": {
        #     "class": "DiscordLogHandler",
        #     "formatter": "discord_info",
        #     "level": logging.INFO
        # }
    },
    "root": {
        "handlers": ("console", "file"),
        "level": "DEBUG"
    }
}

logging.config.dictConfig(LOG_CONFIG)


class SlashBot(discord.Client):

    _module_handler_prefix = "cmd_"

    """
    Bot setup handlers
    """
    def __init__(self):
        super().__init__()

        with open(config.PATHS["discord_creds"], "r") as cf_d:
            config.GLOBAL["discord"] = json.load(cf_d)

        config.GLOBAL["bot"] = self

        # discord_logger = DiscordLogHandler()
        # discord_logger.setLevel(logging.INFO)
        # discord_logger.setFormatter(logging.Formatter("%(message)s"))
        # logging.addHandler(discord_logger)

    def run(self):
        super().run(config.GLOBAL["discord"]["token"])

    def log(self, msg):
        self.send_message(config.GLOBAL["discord"]["log_channel_id"])

    async def activate_modules(self):
        for cmd in CoreFunctions.__dict__.values():
            if isinstance(cmd, type) and issubclass(cmd, Command):
                if len(cmd.command) > 0:
                    self.commands_map[cmd.command] = cmd
                if len(cmd.aliases) > 0:
                    for each in cmd.aliases:
                        self.commands_map[each] = cmd

        for name, module_details in config.MODULES.items():
            if module_details["active"]:
                try:
                    imported_module = importlib.import_module("modules.{}".format(module_details["location"])).__dict__
                    for attribute in imported_module.values():
                        if isinstance(attribute, type) and issubclass(attribute, Command):
                            logging.debug("Iterating {} {}".format(attribute.command, attribute.aliases))
                            if len(attribute.command) > 0:
                                self.commands_map[attribute.command] = attribute
                            if len(attribute.aliases) > 0:
                                for each in attribute.aliases:
                                    self.commands_map[each] = attribute

                    logging.debug("Activated module '{}'".format(name))
                    config.STATS.MODULES_ACTIVE += 1

                except ImportError as ie:
                    logging.exception("Couln't import module '{}'".format(name))

                except Exception as e:
                    logging.debug("{}".format(e))
                    logging.exception("Unkown error activating module {}".format(name))

        logging.info("Registered {} active modules".format(config.STATS.MODULES_ACTIVE))
        logging.debug("Registered commands map is {}".format(self.commands_map))

    async def begin_status_loop(self):
        try:
            if not self._last_status_idx:
                self._last_status_idx = 0
        except AttributeError:
            self._last_status_idx = 0

        if len(config.DISCORD_STATUS_ITER) == 0:
            await self.change_status(game=discord.Game(name="~slash"))
            return

        await self.change_status(game=discord.Game(name=config.DISCORD_STATUS_ITER[self._last_status_idx]))
        threading.Timer(120, self.begin_status_loop).start()

        self._last_status_idx += 1

        if self._last_status_idx >= len(config.DISCORD_STATUS_ITER):
            self._last_status_idx = 0

    """
    Discord event listeners
    """
    async def on_ready(self):
        logging.info("Ready!")
        logging.info("Bot version {}".format(config.VERSION))

        config.STATS = Stats()

        for server in self.servers:
            await self.on_server_join(server)

        self.modules_map = {}
        self.commands_map = {}
        logging.info("Activating modules")
        await self.activate_modules()

    async def on_message(self, message):
        if message.content.startswith(config.BOT_PREFIX):
            config.STATS.PREFIXED_MESSAGES_RECEIVED += 1

        command = message.content[1:].split(" ")[0]

        if command in self.commands_map.keys():
            config.STATS.COMMANDS_RECEIVED += 1

            await self.send_typing(message.channel)

            try:
                # await getattr(self.modules_map[command]["module"], subcommand)(message.author, message.channel, params)
                command = self.commands_map[command](message, defer_response=True)
                await command.make_response()
                response_channel = partial(self.send_message, channel=message.channel)
                self.send_message
                await command.respond(response_channel)
            except errors.BotPermissionError as pe:
                await self.send_error("{} {}".format(message.author.mention, pe), message.channel)
            except errors.SlashBotError as sbe:
                await self.send_error(sbe, message.channel)
            except Exception as e:
                logging.debug("{}: {} error occurred while processing message {}".format(type(e), e, message))
                logging.exception("An error occurred")
                await self.send_error("An error occurred 🙈", message.channel)

    async def on_server_join(self, server):
        config.STATS.SERVERS += 1

        new_server = {
            "server_id": server.id,
            "server_name": server.name,
            "owner": server.owner.id,
            "region": server.region,
            "currently_joined": True,
        }

        server_instance, created = Server.get_or_create(**new_server)
        if not created:
            if server.name != server_instance.server_name:
                logging.debug("Rejoined server, updating name from {} to {}".format(
                    server_instance.server_name,
                    server.name,
                ))
                server_instance.update(server_name=server.name, currently_joined=True).execute()
        else:
            # Only add bot date if it's a new server
            server_instance.update(bot_add_date=datetime.datetime.now())

        for channel in server.channels:
            await self.on_channel_create(channel)

    async def on_server_remove(self, server):
        config.STATS.SERVERS -= 1

        try:
            server_instance = Server.get(server_id=server.id)
            server_instance.currently_joined = False
            server_instance.save()

        except Server.DoesNotExist:
            logging.error("Just left a server that wasn't registered in database! Server ID {}, name {}".format(
                server.id,
                server.name,
            ))

    async def on_channel_create(self, channel):
        if channel.type == discord.ChannelType.text:
            config.STATS.TEXT_CHANNELS += 1
        elif channel.type == discord.ChannelType.voice:
            config.STATS.VOICE_CHANNELS += 1

        new_channel = {
            "channel_id": channel.id,
            "channel_name": channel.name,
            "channel_type": channel.type,
            "server": channel.server.id,
        }

        channel_instance, created = Channel.get_or_create(**new_channel)
        if not created:
            if channel.name != channel_instance.channel_name:
                logging.debug("Updating channel name from {} to {} on server {}".format(
                    channel_instance.channel_name,
                    channel.name,
                    channel.server.name
                ))
                channel_instance.update(channel_name=channel.name).execute()

    async def on_channel_delete(self, channel):
        if channel.type == discord.ChannelType.text:
            config.STATS.TEXT_CHANNELS -= 1
        elif channel.type == discord.ChannelType.voice:
            config.STATS.VOICE_CHANNELS -= 1

    """
    Discord event responders
    """
    async def send_message(self, message, channel):
        await super().send_message(channel, message)
        config.STATS.MESSAGES_SENT += 1

    async def send_error(self, error, channel):
        config.STATS.ERRORS += 1
        await super().send_message(channel, "🚫 **Error:** {}".format(error))

    """
    Destruction
    """
    def __del__(self):
        logging.info("SlashBot exiting")


class CoreFunctions(object):
    async def cmd_stats(self, sender, channel, params):
        await config.GLOBAL["bot"].send_typing(channel)

        uptime = (datetime.datetime.now() - config.STATS.START_TIME).total_seconds()
        uptime_det = {}
        uptime_det["days"] = int(uptime // 86400)
        uptime = uptime - (uptime_det["days"] * 86400)
        uptime_det["hours"] = int(uptime // 3600)
        uptime = uptime - (uptime_det["hours"] * 3600)
        uptime_det["minutes"] = int(uptime // 60)

        await config.GLOBAL["bot"].send_message(channel, (
            "```py\n"
            "Bot version: {version}\n"
            "Bot ID: {bot}\n"
            "Owner ID: {owner}\n"
            "Uptime: {uptime}\n"
            "Commands received: {commands}\n"
            "Messages sent: {messages_sent}\n"
            # "Commands queue size: {commands_queue}"
            "Modules active: {modules}\n"
            "Servers: {servers} | Text channels: {text_channels} | Voice channels: {voice_channels}\n"
            "Errors encountered: {errors}\n"
            "```"
        ).format(
            version=config.VERSION,
            bot=config.GLOBAL["bot"].user.id,
            owner=config.GLOBAL["discord"]["owner_id"],
            uptime="{days} days, {hours} hours, {minutes} minutes".format(**uptime_det),
            commands=config.STATS.COMMANDS_RECEIVED,
            messages_sent=config.STATS.MESSAGES_SENT,
            # commands_queue=None,
            modules=", ".join(config.GLOBAL["bot"].modules_map.keys()),
            servers=config.STATS.SERVERS,
            text_channels=config.STATS.TEXT_CHANNELS,
            voice_channels=config.STATS.VOICE_CHANNELS,
            errors=config.STATS.ERRORS,
        ))


class Stats(object):
    def __init__(self):
        self.START_TIME = datetime.datetime.now()
        self.PREFIXED_MESSAGES_RECEIVED = 0
        self.COMMANDS_RECEIVED = 0
        self.MODULES_ACTIVE = 0
        self.MESSAGES_SENT = 0
        self.SERVERS = 0
        self.TEXT_CHANNELS = 0
        self.VOICE_CHANNELS = 0
        self.ERRORS = 0

    def serialise(self):
        serial = {}

        for attr, val in self.__dict__.items():
            if attr.startswith("__") or attr.endswith("__"):
                continue

            serial[attr] = val

        return serial


class DiscordLogHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        try:
            msg = self.format(record)
            config.GLOBAL["bot"].log(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


if __name__ == "__main__":
    logging.info("Initialising SlashBot")
    SlashBot().run()

    BotStats.create(run_time=str(time.time()), stats_str=json.dumps(config.STATS.serialise()))
