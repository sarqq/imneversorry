from telegram import Update
from telegram.ext import CallbackContext
import collections
import math
import time

import telegram

import db

extract_uid = lambda update: update.message.from_user["id"]
extract_chatid = lambda update: update.message.chat_id
poista_skandit = lambda s: s.replace("ä", "a").replace("Ä", "A").replace("ö", "o").replace("Ö", "O")

class Laji:
    def __init__(self, monikko, kerroin):
        self.monikko = monikko
        self.kerroin = kerroin

    def listauskasky(self):
        return poista_skandit(self.monikko)

class Kilometri:
    lajit = {
        "kavely": Laji("kävelyt", 1),
        "juoksu": Laji("juoksut", 2),
        "pyoraily": Laji("pyöräilyt", 0.8),
        "hiihto": Laji("hiihdot", 1.8),
        "uinti": Laji("uinnit", 3),
    }

    def __init__(self):
        self.commands = {
            'pisteet': self.pisteetHandler,
            'kmstats': self.statsHandler,
            'kmhelp': self.helpHandler,
        }

        for lajinnimi, laji in self.lajit.items():
            db.lisaaUrheilulaji(lajinnimi, laji.kerroin)
            listauskasky = laji.listauskasky()

            lisaa, listaa = self.genLajiHandlerit(lajinnimi)
            self.commands[lajinnimi] = lisaa
            self.commands[listauskasky] = listaa

        self.helptext = "Komennot, kokeile ilman parametria jos et ole varma:\n%s\n\nLajikohtaiset kertoimet:\n%s" % (
            "\n".join("/%s" % s for s in self.commands.keys()),
            "\n".join("%s: %.1f pistettä/km" % (nimi, laji.kerroin) for nimi, laji in self.lajit.items())
        )

    def getCommands(self):
        return self.commands

    def genLajiHandlerit(self, lajinnimi):
        def urh(*args, **kwargs):
            self.urheilinHandler(lajinnimi, *args, **kwargs)

        def get(*args, **kwargs):
            self.getStatHandler(lajinnimi, *args, **kwargs)

        return (urh, get)

    def userFromUid(self, update: Update, context: CallbackContext, uid):
        chat_id = extract_chatid(update)
        return context.bot.get_chat_member(chat_id, uid).user

    def nameFromUid(self, update: Update, context: CallbackContext, uid):
        try:
            user = self.userFromUid(update, context, uid)
            if (user.username is None):
                return "%s %s" % (str(user.first_name), str(user.last_name))
            return user.username

        except telegram.TelegramError:
            return "(None)"

    def parsiAikaLkm(self, args):
        aikasuureet = {
            "s":   1,
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

        aika = 3 * aikasuureet["kk"]
        aikanimi = "3kk"
        lkm = 30

        for arg in args:
            try:
                lkm = int(arg)
                continue
            except ValueError:
                pass

            for lyhenne, kerroin in aikasuureet.items():
                if (arg.endswith(lyhenne)):
                    try:
                        aika = float(arg.rstrip(lyhenne)) * kerroin
                        aikanimi = arg
                        break
                    except ValueError:
                        pass
            else:
                raise ValueError("Unrecognized '%s' in args" % arg)

        return (aika, aikanimi, lkm)

    def urheilinHandler(self, lajinnimi, update: Update, context: CallbackContext):
        def printUsage():
            usage = "Usage: /%s <km>" % lajinnimi
            context.bot.sendMessage(chat_id=update.message.chat_id, text=usage)

        invalidDistance = lambda km: math.isnan(km) or math.isinf(km)

        if (len(context.args) != 1):
            printUsage()
            return

        uid = extract_uid(update)
        chatid = extract_chatid(update)
        try:
            km = float(context.args[0].rstrip("km"))
            if (invalidDistance(km)):
                raise ValueError("invalid distance %f" % km)
        except ValueError:
            printUsage()
            return

        now = int(time.time())
        db.addUrheilu(uid, chatid, km, lajinnimi, now)

    def getStatHandler(self, lajinnimi, update: Update, context: CallbackContext):
        def printUsage(komento):
            usage = "Usage: /%s [lkm] [ajalta]" % komento
            context.bot.sendMessage(chat_id=update.message.chat_id, text=usage)

        laji = self.lajit[lajinnimi]
        try:
            aika, aikanimi, lkm = self.parsiAikaLkm(context.args)
        except ValueError:
            printUsage(laji.listauskasky())
            return

        alkaen = time.time() - aika
        chatid = extract_chatid(update)

        top_suoritukset = db.getTopUrheilut(chatid, lajinnimi, alkaen, lkm)
        lista = "\n".join("%s: %.1f km" %
                (self.nameFromUid(update, context, uid), km)
            for uid, km in top_suoritukset)

        context.bot.sendMessage(chat_id=update.message.chat_id,
            text="Top %i %s viimeisen %s aikana:\n\n%s" %
                (lkm, laji.monikko, aikanimi, lista))

    def pisteetHandler(self, update: Update, context: CallbackContext):
        def usage():
            context.bot.sendMessage(chat_id=update.message.chat_id,
                text="Usage: /pisteet [ajalta]")
        try:
            aika, aikanimi, lkm = self.parsiAikaLkm(context.args)
        except ValueError:
            usage()
            return

        alkaen = time.time() - aika
        chatid = extract_chatid(update)
        pisteet = db.getPisteet(chatid, alkaen, lkm)
        piste_str = "\n".join("%s: %.1f pistettä" %
            (self.nameFromUid(update, context, uid), p) for uid, p in pisteet)

        msg = "Top %i pisteet viimeisen %s aikana:\n\n%s" % (
            lkm, aikanimi, piste_str)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=msg)

    def statsHandler(self, update: Update, context: CallbackContext):
        def usage():
            context.bot.sendMessage(chat_id=update.message.chat_id,
                text="Usage: /kmstats [ajalta]")

        try:
            aika, aikanimi, _ = self.parsiAikaLkm(context.args)
        except ValueError:
            usage()
            return

        alkaen = time.time() - aika
        uid = extract_uid(update)
        chatid = extract_chatid(update)
        name = self.nameFromUid(update, context, uid)

        stats = db.getKayttajanUrheilut(uid, chatid, alkaen)
        lajikohtaiset = ((lajinnimi, km) for lajinnimi, km, _ in stats)
        pisteet = sum(pisteet for _, _, pisteet in stats)

        lajit_str = ", ".join("%s %.1f km" % ln_km for ln_km in lajikohtaiset)
        stat_str = ("%s: Viimeisen %s aikana %.1f pistettä\n\n%s" %
            (name, aikanimi, pisteet, lajit_str))

        context.bot.sendMessage(chat_id=update.message.chat_id,
                        text=stat_str)

    def helpHandler(self, update: Update, context: CallbackContext):
        context.bot.sendMessage(chat_id=update.message.chat_id, text=self.helptext)

    def messageHandler(self, update: Update, context: CallbackContext):
        return
