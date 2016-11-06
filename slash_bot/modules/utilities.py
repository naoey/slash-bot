# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging

import config

from errors import *
from models import *
from commands import *
from utils import *

logger = logging.getLogger(__name__)


class SetLocation(Command):
    command = "setlocation"
    aliases = ["setloc", ]

    @overrides(Command)
    async def make_response(self):
        await super().make_response()

        if len(self.params) == 0:
            raise CommandFormatError("Gib me some location")

        location = self.params[0] if len(self.params) == 1 else " ".join(self.params)
        r = User.update(stored_location=location).where(User.user_id == self.invoker.id).execute()
        if r == 1:
            self.response = "Stored {location} as your location {user}".format(location=location, user=self.invoker.mention)
        else:
            raise SlashBotError("Couldn't store your location", to_be_mentioned=self.invoker.mention)

