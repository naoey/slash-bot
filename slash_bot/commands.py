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
    command = ""
    aliases = []
    required_permissions = []

    def __init__(self, message):
        for each in self.required_permissions:
            if not Permissions.can(message.channel, message.sender, each):
                raise PermissionError(message.sender.mention)

        self._raw_message = message

    async def make_response(self):
        raise NotImplementedError


class Permissions(object):
    BOT_OWNER = 0
    SERVER_OWNER = 1
    SERVER_ADMIN = 2
    CHANNEL_READ = 3
    CHANNEL_WRITE = 4

    @staticmethod
    def can(channel, user, permission):
        """Returns true if a user has a particular permission on a channel.

        Args:
            channel (discord.Channel): The channel on which the permission needs to be evaluated
            user (discord.User): The user for whom the permission needs to be evaluated
            permission (int): The Permission which needs to be evaluated
        Returns:
            bool: True if the user has permission, false if they don't

        """
        pass
