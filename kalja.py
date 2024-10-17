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

#class constructor
class Kalja:
  #TODO: members, getters, setters, other methods
  def __init__(self):
    #TODO: implement
    self.__commands = {
        "juo" : self.beer_handler,
        "kaljat" : self.score_handler,
        "beerstats" : self.stats_handler,
        "beerhelp" : self.help_handler}

    self.__helptext = ""    #TODO: parse
        
    #TODO: getters
    def get_commands(self):
        return self.__commands

    def get_helptext(self):
        return self.__helptext
    
    def user_fom_uid(self, update: Update, context: CallbackContext, uid):
        chat_id = extract_chatid(update)
        return context.bot.get_chat_member(chat_id, uid).user

    def name_from_uid(self, update: Update, context: CallbackContext, uid):
        try:
            user = self.user_from_uid(update, context, uid)
            if (user.username is None):
                return "%s %s" % (str(user.first_name), str(user.last_name))
            return user.username

        except telegram.TelegramError:
            return "(None)"

    def parse_time_num(self, args):
        time_vars = {
            "s":  1,
            "sek": 1,
            "m":   60,
            "min": 60,
            "h":   60 * 60,
            "pv":  60 * 60 * 24,
            "d":   60 * 60 * 24,
            "kk":  60 * 60 * 24 * 30,
            "mo":  60 * 60 * 24 * 30,
            "v":   60 * 60 * 24 * 30 * 365,
            "y":   60 * 60 * 24 * 30 * 365,
        }

        time = 3 * time_vars["kk"]
        time_label = "3kk"
        num = 30

        for arg in args:
            try:
                num = int(arg)
                continue
            except ValueError:
                pass

            for abbr, seconds in time_vars.items():
                if (arg.endswith(abbr)):
                    try:
                        time = float(arg.rstrip(abbr)) * seconds
                        time_label = arg
                        break
                    except ValueError:
                        pass
            else:
                raise ValueError("Unrecognized '%s' in args" % arg)

        return (time, time_label, num)

    def get_stats_handler(self, update: Update, context: CallbackContext):
        #TODO
        
    def score_handler(self, update: Update, context: CallbackContext):
        #TODO

    def stats_handler(self, update: Update, context: CallbackContext):
        #TODO
    
    def help_handler(self, update: Update, context: CallbackContext):
        context.bot.sendMessage(chat_id = update.message.chat_id, text = self.get_helptext())

    def messageHandler(self, update: Update, context: CallbackContext):
        return
