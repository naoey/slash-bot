# coding: utf-8

"""
Created on 2016-08-23
@author: naoey
"""

import logging
import requests
import urllib
import json

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


class Weather(Command):
    command = "weather"
    aliases = ["w", "we", ]

    @overrides(Command)
    async def make_response(self):
        await super().make_response()

        if len(self.params) == 0:
            location = User.get(user_id=self.invoker.id).stored_location
        else:
            location = self.params[0] if len(self.params) == 1 else " ".join(self.params)

        self.response = await self._get_weather(location)

    @staticmethod
    async def _get_weather(location):
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=’London, GB’)&format=json"
        yql_url = baseurl + urllib.parse.urlencode({'q': yql_query, 'u': 'c'}) + "&format=json"
        data = requests.get(yql_url).json()
        return data
