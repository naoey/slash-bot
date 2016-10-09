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

import config
import errors
import models
import utils


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
        self.modules_map = {}

        self.modules_map["bot"] = {
            "module": CoreFunctions(),
            "subcommands": [x for x, y in CoreFunctions.__dict__.items() if (
                type(y) == type(lambda:0) and x.startswith("cmd_"))]
        }

        for name, module_details in config.MODULES.items():
            if module_details["active"]:
                try:
                    imported_module = importlib.import_module("modules.{}".format(module_details["location"]))
                    main_class = getattr(imported_module, module_details["class"])

                    self.modules_map[module_details["prefix"]] = {
                        "module": main_class(),
                        "subcommands": [x for x, y in main_class.__dict__.items() if (
                            type(y) == type(lambda:0) and x.startswith("cmd_"))],
                    }

                    logging.debug("Activated module '{}".format(name))
                    config.STATS.MODULES_ACTIVE += 1

                except ImportError as ie:
                    logging.exception("Couldn't import module '{}'".format(name))

                except Exception as e:
                    logging.debug("{}".format(e))
                    logging.exception("Unkown error activating module {}".format(name))

        logging.info("Registered {} active modules".format(config.STATS.MODULES_ACTIVE))
        logging.debug("Registered modules map is {}".format(self.modules_map))

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
        config.STATS.SERVERS = len(self.servers)

        self.modules_map = {}

        logging.info("Activating modules")
        await self.activate_modules()

        for server in self.servers:
            for channel in server.channels:
                if channel.type == "text":
                    config.STATS.TEXT_CHANNELS += 1
                elif channel.type == "voice":
                    config.STATS.VOICE_CHANNELS += 1

        # await self.begin_status_loop()

    async def on_message(self, message):
        if message.content.startswith(config.BOT_PREFIX):
            config.STATS.PREFIXED_MESSAGES_RECEIVED += 1

            params = message.content[1:].split(" ")
            command = params.pop(0)
            subcommand = self._module_handler_prefix + params.pop(0)

            if command in self.modules_map and subcommand in self.modules_map[command]["subcommands"]:
                config.STATS.COMMANDS_RECEIVED += 1

                try:
                    await getattr(self.modules_map[command]["module"], subcommand)(message.author, message.channel, params)
                except errors.SlashBotError as sbe:
                    await self.send_error(message.channel, sbe)
                except Exception as e:
                    logging.debug("{}: {} error occurred while processing message {}".format(type(e), e, message))
                    logging.exception("An error occurred")
                    await self.send_error(message.channel, "An error occurred 🙈")

    """
    Discord event responders
    """
    async def send_message(self, channel, message):
        config.STATS.MESSAGES_SENT += 1
        await super().send_message(channel, message)

    async def send_error(self, channel, error):
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

    models.BotStats.create(run_time=str(time.time()), stats_str=json.dumps(config.STATS.serialise()))
