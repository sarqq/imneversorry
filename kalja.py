"""
@Author: sarqq
Adds database entry for beers drunk by group members.
Add new beer with command "juo", with optional parameter number_of_beers.
"""

from telegram import Update
from telegram.ext import CallbackContext
import collections
import math
import time

import telegram
import db

#lambdas
extract_uid = lambda update: update.message.from_user["id"]
extract_chatid = lambda update: update.message.chat_id
poista_skandit = lambda s: s.replace("ä", "a").replace("Ä", "A").replace("ö", "o").replace("Ö", "O")

#class constructor
class Kalja:
  #TODO: members, getters, setters, other methods
  def __init__(self):
    #TODO: implement
    self.__commands = {
      "juo" : None,
      "beerstats" : None,
      "beerhelp" : None}
