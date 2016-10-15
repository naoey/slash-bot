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

    def __init__(self, message, defer_response=False):
        """Create a new command object to process and respond to a command.

        Args:
            message (discord.Message): The Message that triggered this command
            defer_response (bool): If True, the command will not begin working on the response immediately,
                instead it will start its work when the response is called for. Defaults to False.

        Raises:
            PermissionError: If the user who invoked the command doesn't have the necessary permissions or roles

        """
        found_role_permission = False
        if len(required_roles) > 0:
            for each in required_roles:
                if Permissions.can(message.channel, message.sender, role=each):
                    found_role_permission = True
                    break

        found_permission = False
        if len(required_permissions) > 0:
            for each in required_permissions:
                if Permissions.can(message.channel, message.sender, permission=each):
                    found_permission = True
                    break

        if not found_role_permission and not found_permission:
            raise PermissionError("You don't have the necessary permission!")

        self._raw_message = message
        self.response = None

        if not defer_response:
            self.make_response()

    def make_response(self):
        """Override this method to do whatever work the command needs to do and store it in `response`."""
        raise NotImplementedError

    async def respond(self, callback):
        """Don't override this method. It is called by the bot to send the response when it is ready to."""
        if self.response is None:
            self.make_response()

        await callback(response)


class Permissions(object):
    BOT_OWNER = 0
    SERVER_OWNER = 1
    BOT_ADMIN = 2
    SERVER_ADMIN = 3

    @staticmethod
    def can(channel, user, permission=None, role=None):
        """Returns true if a user has a particular permission on a channel.

        For resolving permissions by roles, the `user` has to be a `discord.Member` object. If both `role`
        and `permission` are given, the permission is resolved as an or operation.

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
            return role in user.roles

        if permission == self.BOT_OWNER:
            return user.id == config.GLOBAL["discord"]["owner_id"]
        if permission == self.SERVER_OWNER:
            return user.id == channel.server.owner.id
