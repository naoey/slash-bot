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
    resposne_chunk_marker = "$##$"

    command = ""
    aliases = []
    required_permissions = []
    required_roles = []

    def __init__(self, message):
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

    async def respond(self, callback):
        """Do whatever work the command needs and send the response to `callback`

        Override this method in subclasses to implement a command. Use `resposne_chunk_marker` to mark points
        in the response string on which the reponse can be split. This is needed where there is a maximum string
        size in place (ex. Discord has a 2000 character limit). It is better if this is taken care of by the
        command to produce neat responses than have the caller arbitrarily chunk the response.

        Args:
            callback: Call this method with the response string

        """
        raise NotImplementedError


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
