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
    """
    Bot setup handlers
    """
    def __init__(self):
        super().__init__()

        CredentialsManager(config.PATHS["credentials_file"])

        config.GLOBAL["bot"] = self

        self._channel_message_subscriptions = {}

        # discord_logger = DiscordLogHandler()
        # discord_logger.setLevel(logging.INFO)
        # discord_logger.setFormatter(logging.Formatter("%(message)s"))
        # logging.addHandler(discord_logger)

    def run(self):
        super().run(config.GLOBAL["credentials"]["discord"]["token"])

    def log(self, msg):
        self.send_message(config.GLOBAL["credentials"]["discord"]["log_channel_id"])

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
                    imported_module = importlib.import_module("modules.{}".format(module_details["location"]))
                    commands_in_module = [
                        v for k, v in imported_module.__dict__.items() if (
                            isinstance(v, type) and v.__module__ == imported_module.__name__ and issubclass(v, Command)
                        )
                    ]

                    for command in commands_in_module:
                        if len(command.command) > 0:
                            self.commands_map[command.command] = command
                        if len(command.aliases) > 0:
                            for alias in command.aliases:
                                self.commands_map[alias] = command

                    logging.debug("Activated module '{}'".format(name))
                    config.STATS.MODULES_ACTIVE += 1

                except ImportError as ie:
                    logging.exception("Couldn't import module '{}'".format(name))

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
        logging.info("Bot user ID is {}".format(self.user.id))
        logging.info("Bot owner ID is given as {}".format(config.GLOBAL["credentials"]["discord"]["owner_id"]))

        # Store shorter references to some things
        config.GLOBAL["bot_id"] = self.user.id
        config.GLOBAL["owner_id"] = config.GLOBAL["credentials"]["discord"]["owner_id"]
        config.GLOBAL["server_id"] = config.GLOBAL["credentials"]["discord"]["server_id"]

        config.STATS = Stats()

        await self.change_status(game=discord.Game(name=config.DISCORD_STATUS_ITER[0]))

        for server in self.servers:
            await self.on_server_join(server)

        self.modules_map = {}
        self.commands_map = {}
        logging.info("Activating modules")
        await self.activate_modules()

        discord.opus.load_opus("../opus/libopus-0")
        logging.info("Opus loaded is {}".format(discord.opus.is_loaded()))

    async def on_message(self, message):
        if message.channel.id in self._channel_message_subscriptions.keys():
            for each in self._channel_message_subscriptions[message.channel.id].values():
                await each(message=message)

        if message.content.startswith(config.BOT_PREFIX):
            config.STATS.PREFIXED_MESSAGES_RECEIVED += 1

            command = message.content[1:].split(" ")[0]

            if command in self.commands_map.keys():
                config.STATS.COMMANDS_RECEIVED += 1

                try:
                    command = await self.commands_map[command].create_command(message)
                    if command is not None:
                        if not command.silent_permissions:
                            await self.send_typing(message.channel)
                        await command.make_response()
                        response_channel = partial(self.send_message, channel=message.channel)
                        await command.respond(response_channel)
                except errors.SlashBotPermissionError as pe:
                    if not pe.silent:
                        await self.send_error(pe, message.channel)
                except errors.SlashBotError as sbe:
                    await self.send_error(sbe, message.channel)
                except Exception as e:
                    logging.debug("{}: {} error occurred while processing message {}".format(type(e), e, message))
                    logging.exception("An error occurred")
                    await self.send_error(SlashBotError("An error occurred 🙈"), message.channel)

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
    async def send_message(self, message, channel, chunk=False):
        if len(message) >= 2000 or chunk:
            if Command.response_chunk_marker in message:
                messages = message.split(Command.response_chunk_marker)
            else:
                messages = (message[0 + i: 1999 + i] for i in range(0, len(message), 1999))
            for msg in messages:
                await super().send_message(channel, msg)
        else:
            await super().send_message(channel, message)
        config.STATS.MESSAGES_SENT += 1

    async def send_shortlived_message(self, message, channel, duration=5):
        """Send a message that gets deleted after `duration` number of seconds."""
        pass

    async def send_error(self, error, channel):
        config.STATS.ERRORS += 1
        if error.to_be_mentioned is not None:
            await super().send_message(channel, "{}\n🚫 **Error:** {}".format(error.to_be_mentioned, error))
        else:
            await super().send_message(channel, "🚫 **Error:** {}".format(error))

    """
    Subscriptions
    """
    def subscribe_channel_messages(self, channel_id, callback):
        if channel_id not in self._channel_message_subscriptions.keys():
            self._channel_message_subscriptions[channel_id] = {}

        token = channel_id + "_" + random_string()
        while token in self._channel_message_subscriptions[channel_id].keys():
            token = channel_id + "_" + random_string()

        if callable(callback) and channel_id is not None:
            if channel_id in self._channel_message_subscriptions.keys():
                self._channel_message_subscriptions[channel_id][token] = callback

        return token

    def unsubscribe_channel_messages(self, token):
        channel = token.split("_")[0]
        if channel in self._channel_message_subscriptions.keys():
            try:
                del self._channel_message_subscriptions[channel][token]
            except KeyError:
                logging.error("Just tried unsubscribing a non-existent subscription to channel messages")

    """
    Destruction
    """
    def __del__(self):
        logging.info("SlashBot exiting")


class CredentialsManager(dict):
    """Class for storing all API keys and whatnot that can be called on by modules to get their stuff."""
    def __init__(self, path=None):
        if path is None or not path.endswith(".json"):
            raise ValueError("Invalid credentials file. Expected a JSON file.")

        with open(path) as cf:
            super().__init__(json.load(cf))

        config.GLOBAL["credentials"] = self


class CoreFunctions(object):
    class PublicStats(Command):
        command = "stats"
        aliases = ["st", ]

        @overrides(Command)
        async def make_response(self):
            await super().make_response()

            uptime = (datetime.datetime.now() - config.STATS.START_TIME).total_seconds()
            uptime_det = {}
            uptime_det["days"] = int(uptime // 86400)
            uptime = uptime - (uptime_det["days"] * 86400)
            uptime_det["hours"] = int(uptime // 3600)
            uptime = uptime - (uptime_det["hours"] * 3600)
            uptime_det["minutes"] = int(uptime // 60)

            self.response = (
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
                bot=config.GLOBAL["bot_id"],
                owner=config.GLOBAL["owner_id"],
                uptime="{days} day(s), {hours} hour(s), {minutes} minute(s)".format(**uptime_det),
                commands=config.STATS.COMMANDS_RECEIVED,
                messages_sent=config.STATS.MESSAGES_SENT,
                # commands_queue=None,
                modules=config.STATS.MODULES_ACTIVE,
                servers=config.STATS.SERVERS,
                text_channels=config.STATS.TEXT_CHANNELS,
                voice_channels=config.STATS.VOICE_CHANNELS,
                errors=config.STATS.ERRORS,
            )

    class InviteLink(Command):
        command = "invite"
        aliases = ["inv", "invitelink", "add", "addlink", ]
        required_permissions = [PERMISSIONS.BOT_OWNER, ]
        silent_permissions = True

        @overrides(Command)
        async def make_response(self):
            await super().make_response()
            self.response = config.GLOBAL["credentials"]["discord"]["invite_link"]

    class CommandsList(Command):
        command = "commands"
        aliases = ["cl", "help", "h", ]

        @overrides(Command)
        async def make_response(self):
            await super().make_response()
            self.response = "The commands list and usage information is on the bot's GitHub page at {}".format(config.URIS["github"])


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

            if type(val) == datetime.datetime:
                val = val.strftime("%Y-%m-%D %H:%M:%S")

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
