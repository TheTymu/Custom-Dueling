import os
import sys
import json
import time
import random
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

import sqlite3


ScriptName = "[TT] Point Dueling System - SQLite Version 1"
Website = "https://github.com/TheTymu"
Description = "Currently Under Development: SQLite Version 1"
Creator = "TheTymu"
Version = "0.3.00"


Configuration = {}
PendingDuels = []


def Init():
    global Configuration
    global PendingDuels
    SystemDatabase = sqlite3.connect("data.db")
    DuelData = SystemDatabase.cursor()
    DuelData.execute('CREATE TABLE IF NOT EXISTS config (initiate_command text, accept_command text, deny_command text, stats_command text, min_bet integer, cooldown integer, permission text)')
    if DuelData.execute('SELECT * FROM config').fetchone() < 1:
        DuelData.execute('INSERT INTO config (initiate_command, accept_command, deny_command, stats_command, min_bet, cooldown, permission) VALUES ("!duel", "!accept", "!deny", "!stats", 0, 10, "Everyone")')
    DuelData.execute('CREATE TABLE IF NOT EXISTS duels (requestorID text, requestedID text, bet_amount integer, timeRequested integer, duelStatus text)')
    SystemDatabase.commit()

    Configuration = {
        "initiate_command": DuelData.execute('SELECT initiate_command FROM config').fetchone()[0],
        "accept_command":   DuelData.execute('SELECT accept_command FROM config').fetchone()[0],
        "deny_command":     DuelData.execute('SELECT deny_command FROM config').fetchone()[0],
        "stats_command":    DuelData.execute('SELECT stats_command FROM config').fetchone()[0],
        "min_bet":          DuelData.execute('SELECT min_bet FROM config').fetchone()[0],
        "cooldown":         DuelData.execute('SELECT cooldown FROM config').fetchone()[0],
        "permission":       DuelData.execute('SELECT permission FROM config').fetchone()[0]
    }

    return

def Execute(data):
    SystemDatabase = sqlite3.connect("data.db")
    DuelData = SystemDatabase.cursor()

    if data.IsChatMessage() and Parent.HasPermission(data.User, Configuration["permission"], ""):
        requestorID = data.User.lower()
        requestedID = data.GetParam(1).lower()
        chatCommand = data.GetParam(0).lower()
        requestedID = requestedID.replace("@", "")

        if chatCommand == Configuration['initiate_command'] and data.GetParamCount() == 3 and not Parent.IsOnUserCooldown(ScriptName, Configuration['initiate_command'], requestorID):
            if requestedID not in Parent.GetViewerList() or requestedID == data.User:
                Parent.SendStreamMessage(
                    "@" + str(requestorID) + " - " + str(requestedID) + " is not a valid duel user!")
                return
            elif Parent.GetPoints(requestorID) < int(data.GetParam(2)) or Parent.GetPoints(requestorID) < int(Configuration['min_bet']):
                Parent.SendStreamMessage("@" + str(requestorID) + " - " + str(data.GetParam(2)) + " must be an integer value greater than " + str(Configuration['min_bet']) + " and within your amount of " + str(Parent.GetPoints(requestorID)) + " " + str(Parent.GetCurrencyName()) + "(s)!")
                return
            elif int(Parent.GetPoints(requestedID)) < int(data.GetParam(2)):
                Parent.SendStreamMessage("@" + str(requestorID) + " - " + str(requestedID) + " only has " + str(Parent.GetPoints(requestedID)) + " " + str(Parent.GetCurrencyName()) + "(s) total!")
                return
            else:
                PendingDuels = DuelData.execute("SELECT * FROM duels WHERE duelStatus = 'PENDING'").fetchall()
                for each in PendingDuels:
                    if requestorID == each[0] or requestorID == each[1]:
                        Parent.SendStreamMessage("@" + str(requestorID) + ", you are already enrolled on the fight list. Try again later when your listing expires!")
                        return
                    elif requestedID == each[0] or requestedID == each[1]:
                        Parent.SendStreamMessage("@" + str(requestorID) + ", " + str(requestedID) + " is already enrolled to fight, try again later once their listing expires!")
                        return

                DuelData.execute("INSERT INTO duels (requestorID, requestedID, bet_amount, timeRequested, duelStatus) VALUES ('" + str(requestorID) + "','" + str(requestedID) + "','" + data.GetParam(2) + "','" + str(time.time()) + "','" + str('PENDING') + "')")
                SystemDatabase.commit()

                Parent.SendStreamMessage("@" + str(requestedID) + " you have been challenged to a fight to the death by @" + str(requestorID) + "! They have bet " + str(data.GetParam(2)) + " " + str(Parent.GetCurrencyName()) + "(s) they will win! You have 2 minutes to !accept the challenge.")
                return

        elif data.GetParam(0) == Configuration['accept_command']:
            PendingDuels = DuelData.execute("SELECT * FROM duels WHERE duelStatus = 'PENDING'").fetchall()
            for each in PendingDuels:
                if each[1] == data.User:
                    Parent.AddUserCooldown(str(ScriptName), str(Configuration['initiate_command']), str(each[0]), int(Configuration['cooldown']))
                    if bool(random.getrandbits(1)):
                        Parent.SendStreamMessage("The glorious battle has ended and @" + str(
                            data.User) + " has risen victorious striking @" + str(each[0]) + " down for " +
                                                 str(each[2]) + " " + str(Parent.GetCurrencyName()) + "(s)!")
                        Parent.AddPoints(data.User, int(each[2]))
                        Parent.RemovePoints(each[0], int(each[2]))
                        DuelData.execute("UPDATE duels SET duelStatus='REQUESTED_USER_WON' WHERE timeRequested='" + str(each[3]) + "' AND requestedID='" + data.User + "'")
                        SystemDatabase.commit()
                    else:
                        Parent.SendStreamMessage("The glorious battle has ended and @" + str(
                            each[0]) + " has risen victorious striking @" + str(data.User) + " down for " +
                                                 str(each[2]) + " " + str(Parent.GetCurrencyName()) + "(s)!")
                        Parent.AddPoints(each[0], int(each[2]))
                        Parent.RemovePoints(data.User, int(each[2]))
                        DuelData.execute("UPDATE duels SET duelStatus='REQUESTOR_USER_WON' WHERE timeRequested='" + str(each[3]) + "' AND requestedID='" + data.User + "'")
                        SystemDatabase.commit()
                    return
        elif data.GetParam(0) == Configuration['deny_command']:
            for each in PendingDuels:
                if each[1] == data.User:
                    Parent.SendStreamMessage("@" + (str(data.User)) + " has declined @" + str(
                        each[0]) + " duel request and now walks with shame.")
                    DuelData.execute("UPDATE duels SET duelStatus='REQUEST_DECLINED' WHERE timeRequested='" + str(each[3]) + "' AND requestedID='" + data.User + "'")
                    SystemDatabase.commit()
        elif data.GetParam(0) == Configuration['stats_command']:
            if data.GetParamCount() == 1:
                TotalDuels = DuelData.execute("SELECT COUNT(*) FROM duels WHERE duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()[0]
                TotalBet = DuelData.execute("SELECT SUM(bet_amount) FROM duels WHERE duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()[0]
                HighestBet = DuelData.execute("SELECT MAX(bet_amount), requestorID FROM duels WHERE duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()
                RequestorWinCount = DuelData.execute("SELECT COUNT(*) FROM duels WHERE duelStatus = 'REQUESTOR_USER_WON'").fetchone()[0]
                RequestorLossCount = DuelData.execute("SELECT COUNT(*) FROM duels WHERE duelStatus = 'REQUESTED_USER_WON'").fetchone()[0]
                AVG_WIN = RequestorWinCount/float(TotalDuels) * 100
                AVG_LOSS = RequestorLossCount/float(TotalDuels) * 100

                Parent.SendStreamMessage("There have been " + str(TotalDuels) + " duel(s) and " + str(TotalBet) + " " + str(Parent.GetCurrencyName()) + "(s) bet in total! The biggest bet ever made is " + str(HighestBet[0])  + " " + str(Parent.GetCurrencyName()) + "(s) by " + str(HighestBet[1]) + "! The average chance to win a bet is " + str(AVG_WIN) + "% making your chance of losing " + str(AVG_LOSS) + "%!")
            elif data.GetParamCount() == 2:
                UserDuels = DuelData.execute("SELECT COUNT(*) FROM duels WHERE requestorID == '" + str(requestedID) + "' or requestedID == '" + str(requestedID) + "' AND duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()[0]
                if UserDuels < 1:
                    Parent.SendStreamMessage("@" + str(requestedID) + " has never competed in a duel before!")
                UserTotalBet = DuelData.execute("SELECT SUM(bet_amount) FROM duels WHERE requestorID == '" + str(requestedID) + "' or requestedID == '" + str(requestedID) + "' AND duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()[0]
                UserHighestBet = DuelData.execute("SELECT MAX(bet_amount) FROM duels WHERE requestorID == '" + str(requestedID) + "' AND duelStatus <> 'REQUEST_DECLINED' AND duelStatus <> 'PENDING'").fetchone()[0]
                UserBiggestRequestorWin = DuelData.execute("SELECT MAX(bet_amount) FROM duels WHERE requestorID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTOR_USER_WON'").fetchone()[0]
                UserBiggestRequestedWin = DuelData.execute("SELECT MAX(bet_amount) FROM duels WHERE requestedID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTED_USER_WON'").fetchone()[0]
                UserBiggestRequestedLoss = DuelData.execute("SELECT MAX(bet_amount) FROM duels WHERE requestorID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTED_USER_WON'").fetchone()[0]
                UserBiggestRequestorLoss = DuelData.execute("SELECT MAX(bet_amount) FROM duels WHERE requestedID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTOR_USER_WON'").fetchone()[0]
                UserRequestorWinRate = DuelData.execute("SELECT COUNT(*) FROM duels WHERE requestorID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTOR_USER_WON'").fetchone()[0]
                UserRequestedWinRate = DuelData.execute("SELECT COUNT(*) FROM duels WHERE requestedID == '" + str(requestedID) + "' AND duelStatus = 'REQUESTED_USER_WON'").fetchone()[0]

                USER_AVG_WIN = UserRequestedWinRate + UserRequestorWinRate / float(UserDuels) * 100

                if UserBiggestRequestedWin > UserBiggestRequestorWin:
                    UserBiggestWin = UserBiggestRequestedWin
                else:
                    UserBiggestWin = UserBiggestRequestorWin

                if UserBiggestRequestedLoss > UserBiggestRequestorLoss:
                    UserBiggestLoss = UserBiggestRequestedLoss
                else:
                    UserBiggestLoss = UserBiggestRequestorLoss
                Parent.SendStreamMessage("@" + str(requestedID) + " has been in " + str(UserDuels) + " duel(s) and has bet " + str(UserTotalBet) + " " + str(Parent.GetCurrencyName()) + "(s) in overall! The biggest bet they have ever made is " + str(UserHighestBet) + " " + str(Parent.GetCurrencyName()) + "(s). Their biggest win is " + str(UserBiggestWin) + " " + str(Parent.GetCurrencyName()) + "(s) and their biggest loss is " + str(UserBiggestLoss) + " " + str(Parent.GetCurrencyName()) + "(s). They have a win rate of " + str(USER_AVG_WIN) + "%!")
            return
    return

def Tick():
    SystemDatabase = sqlite3.connect("data.db")
    DuelData = SystemDatabase.cursor()
    PendingDuels = DuelData.execute("SELECT * FROM duels WHERE duelStatus = 'PENDING'").fetchall()
    for each in PendingDuels:
        if(time.time() - int(each[3]) > 120):
            DuelData.execute("UPDATE duels SET duelStatus='REQUEST_DECLINED' WHERE timeRequested='" + str(each[3]) + "'")
            SystemDatabase.commit()

    return

def Parse():
    return


def ReloadSettings(jsonData):
    SystemDatabase = sqlite3.connect("data.db")
    DuelData = SystemDatabase.cursor()
    jsonData = json.loads(jsonData)
    DuelData.execute('UPDATE config SET initiate_command = "' + str(jsonData['initiate_command']) + '"')
    DuelData.execute('UPDATE config SET accept_command = "' + str(jsonData['accept_command']) + '"')
    DuelData.execute('UPDATE config SET deny_command = "' + str(jsonData['deny_command']) + '"')
    DuelData.execute('UPDATE config SET stats_command = "' + str(jsonData['stats_command']) + '"')
    DuelData.execute('UPDATE config SET min_bet = "' + str(jsonData['min_bet']) + '"')
    DuelData.execute('UPDATE config SET cooldown = "' + str(jsonData['cooldown']) + '"')
    DuelData.execute('UPDATE config SET permission = "' + str(jsonData['permission']) + '"')
    SystemDatabase.commit()

    Configuration = {
        "initiate_command": DuelData.execute('SELECT initiate_command FROM config').fetchone()[0],
        "accept_command":   DuelData.execute('SELECT accept_command FROM config').fetchone()[0],
        "deny_command":     DuelData.execute('SELECT deny_command FROM config').fetchone()[0],
        "stats_command":    DuelData.execute('SELECT stats_command FROM config').fetchone()[0],
        "min_bet":          DuelData.execute('SELECT min_bet FROM config').fetchone()[0],
        "cooldown":         DuelData.execute('SELECT cooldown FROM config').fetchone()[0],
        "permission":       DuelData.execute('SELECT permission FROM config').fetchone()[0]
    }
    return

def Unload():
    return

def ScriptToggled(state):
    return