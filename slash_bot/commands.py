# coding: utf-8

"""
Created on 2016-10-12
@author: naoey
"""

import logging
import datetime

from errors import *
from models import *

logger = logging.getLogger(__name__)


class Command(object):
    """The base command class

    Every SlashBot command must inherit from this class to be recognised as a command and added to the
    bot's commands mapping. Override the `make_response()` method to do whatever work needs to be done to
    generate the command's resposne. The bot will handle sending the response when it is ready to.

    Use `response_chunk_marker` in the overridden `make_response()` if the response length exceeds 2000
    characters. Discord imposes a 2000 character limit to messsages. It is better for each command to
    chunk its response neatly than have it arbitrarily chunked by the bot.

    """
    response_chunk_marker = "$##$"

    command = ""
    aliases = []
    required_permissions = []
    required_roles = []

    def __init__(self, message):
        """Don't do this. Use `create_command()` instead.

        Args:
            message (discord.Message): The Message that triggered this command
            defer_response (bool): If True, the command will not begin working on the response immediately,
                instead it will start its work when the response is called for. Defaults to False.

        """
        self._raw_message = message
        self.response = ""

        self.source_channel = message.channel
        self.invoker = message.author
        self.params = []

        params = message.content.split(" ")[1:]
        idx = 0
        while idx < len(params):
            if params[idx].startswith("\"") or params[idx].startswith("'"):
                terminus = params[idx][0]
                string = params[idx][1:]
                idx += 1
                while idx < len(params):
                    if params[idx].endswith(terminus):
                        string += " {}".format(params[idx])[:-1]
                        idx += 1
                        break
                    string += " {}".format(params[idx])
                    idx += 1

                self.params.append(string)
            else:
                self.params.append(params[idx])
                idx += 1

    @classmethod
    async def create_command(cls, message):
        """Use this to create commands so that commands that may have subcommands can return the appropriate
        type of command.

        Commands must override this method

        Returns:
            command (Command): A subclass of Command

        """
        return cls(message)

    async def make_response(self):
        """Override this method to do whatever work the command needs to do and store it in `response`.

        Remember to call super().make_response() to resolve permissions for the command.

        Raises:
            PermissionError: If the user who invoked the command doesn't have the necessary permissions or roles

        """
        found_role_permission = False
        if len(self.required_roles) > 0:
            for each in self.required_roles:
                if Permissions.can(self.source_channel, self.invoker, role=each):
                    found_role_permission = True
                    break

        found_permission = False
        if len(self.required_permissions) > 0:
            for each in self.required_permissions:
                if Permissions.can(self.source_channel, self.invoker, permission=each):
                    found_permission = True
                    break

        if ((len(self.required_roles) > 0 and not found_role_permission) and
                (len(self.required_permissions) > 0 and not found_permission)):
            raise BotPermissionError("You don't have the necessary permission!")

    async def respond(self, callback):
        """Called by the bot to send the response when it is ready to."""
        if self.response == "":
            await self.make_response()
        if self.response is not None:
            await callback(self.response)


class Permissions(object):
    BOT_OWNER = 0
    SERVER_OWNER = 1
    BOT_ADMIN = 2
    SERVER_ADMIN = 3

    @staticmethod
    def can(channel, user, permission=None, role=None):
        """Returns true if a user has a particular permission on a channel.

        For resolving permissions by roles, the `user` has to be a `discord.Member` object. If both `role`
        and `permission` are given, the permission is resolved as an AND operation.

        Args:
            channel (discord.Channel): The channel on which the permission needs to be evaluated
            user (discord.User): The user for whom the permission needs to be evaluated
            permission (int): The Permission which needs to be evaluated
            role (discord.Role): The role that the user must have
        Returns:
            bool: True if the user has permission, False if they don't
        Raises:
            AttributeError: If permission is being resolved by role and the given user was not of type
                `discord.Member`

        """
        if permission is None and role is None:
            return True

        if role is not None:
            role_permission = role.lower() in [r.name.lower() for r in user.roles]
        else:
            role_permission = True

        if permission is None:
            return role_permission
        if permission == Permissions.BOT_OWNER:
            return role_permission and user.id == config.GLOBAL["discord"]["owner_id"]
        if permission == Permissions.SERVER_OWNER:
            return role_permission and user.id == channel.server.owner.id
        if permission == Permissions.SERVER_ADMIN:
            return role_permission and user.permissions_in(channel).administrator
