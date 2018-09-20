# ---------------------------
#   Import Libraries
# ---------------------------
import json
import random
import time

# ---------------------------
#   [Required] Script Information
# ---------------------------


ScriptName = "[TT] Point Dueling System"
Website = "https://www.twitter.com/thetymu"
Description = "Development Edition - Working Order"
Creator = "TheTymu"
Version = "0.2.18"

# ---------------------------
#   Define Global Variables
# ---------------------------


Configuration = {}
DuelStats = {}
PendingDuels = []


# ---------------------------
#   [Required] Initialize Data (Only called on load)
# ---------------------------


def Init():
    global Configuration
    global PendingDuels
    global DuelStats
    try:
        with open('config.json', mode='r') as config:
            Configuration = json.load(config, encoding='utf-8-sig')
    except:
        Configuration = {
            "initiate_command": "!duel",
            "accept_command": "!accept",
            "deny_command": "!decline",
            "min_bet": 0,
            "cooldown": 30,
            "permission": "Everyone"
        }

        with open('config.json', mode='w+') as config:
            json.dump(Configuration, config)

    return


# ---------------------------
#   [Required] Execute Data / Process messages
# ---------------------------


def Execute(data):
    if data.IsChatMessage() and Parent.HasPermission(data.User, Configuration["permission"], ""):
        if data.GetParam(0) == Configuration[
            'initiate_command'] and data.GetParamCount() == 3 and not Parent.IsOnUserCooldown(ScriptName, Configuration[
            'initiate_command'], data.User):
            if data.GetParam(1).lower() not in Parent.GetViewerList() or data.GetParam(1).lower() == data.User:
                Parent.SendStreamMessage(
                    "@" + str(data.User) + " - " + str(data.GetParam(1)) + " is not a valid duel user!")
                return
            elif Parent.GetPoints(data.User) < int(
                    data.GetParam(2) or Parent.GetPoints(data.User) < int(Configuration['min_bet'])):
                Parent.SendStreamMessage("@" + str(data.User) + " - " + str(
                    data.GetParam(2)) + " must be an integer value greater than " + str(
                    Configuration['min_bet']) + " and within your amount of " + str(
                    Parent.GetPoints(data.User)) + " " + str(Parent.GetCurrencyName()) + "(s)!")
                return
            elif int(Parent.GetPoints(data.GetParam(1).lower())) < int(data.GetParam(2)):
                Parent.SendStreamMessage("@" + str(data.User) + " - " + str(data.GetParam(1)) + " only has " + str(
                    Parent.GetPoints(data.GetParam(1).lower())) + " " + str(Parent.GetCurrencyName()) + "(s) total!")
                return
            else:
                duel_object = {
                    "requestorID": data.User.lower(),
                    "requestedID": data.GetParam(1).lower(),
                    "bet": data.GetParam(2),
                    "timeRequested": time.time()
                }

                for each in PendingDuels:
                    if data.User == each['requestorID'] or data.User == each['requestedID']:
                        Parent.SendStreamMessage(
                            "You are already enrolled on the fight list, try again later when your listing expires!")
                        return
                    elif data.GetParam(1) == each['requestorID'] or data.GetParam(1) == each['requestedID']:
                        Parent.SendStreamMessage("@" + str(data.User) + ", " + str(data.GetParam(
                            1)) + " is already enrolled to fight, try again later once their listing expires!")
                        return

                PendingDuels.append(duel_object)
                Parent.SendStreamMessage(
                    "@" + str(data.GetParam(1)) + " you have been challenged to a fight to the death by @" + str(
                        data.User) + "! They have bet " + str(data.GetParam(2)) + " " + str(
                        Parent.GetCurrencyName()) + "(s) they will win! You have 2 minutes to !accept the challenge.")
                return

        elif data.GetParam(0) == Configuration['accept_command']:
            for each in PendingDuels:
                if each['requestedID'] == data.User:
                    PendingDuels.remove(each)
                    Parent.AddUserCooldown(str(ScriptName), str(Configuration['initiate_command']),
                                           str(each['requestorID']), int(Configuration['cooldown']))
                    if bool(random.getrandbits(1)):
                        Parent.SendStreamMessage("The glorious battle has ended and @" + str(
                            data.User) + " has risen victorious striking @" + str(each['requestorID']) + " down for " +
                                                 each['bet'] + " " + str(Parent.GetCurrencyName()) + "(s)!")
                        Parent.AddPoints(data.User, int(each['bet']))
                        Parent.RemovePoints(each['requestorID'], int(each['bet']))
                    else:
                        Parent.SendStreamMessage("The glorious battle has ended and @" + str(
                            each['requestorID']) + " has risen victorious striking @" + str(data.User) + " down for " +
                                                 each['bet'] + " " + str(Parent.GetCurrencyName()) + "(s)!")
                        Parent.AddPoints(each['requestorID'], int(each['bet']))
                        Parent.RemovePoints(data.User, int(each['bet']))
                    return
        elif data.GetParam(0) == Configuration['deny_command']:
            for each in PendingDuels:
                if each['requestedID'] == data.User:
                    PendingDuels.remove(each)
                    Parent.SendStreamMessage("@" + (str(data.User)) + " has declined @" + str(
                        each['requestorID']) + " duel request and now walks with shame.")
    return


# ---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
# ---------------------------


def Tick():
    Parent.Log('Duel Script Pending', str(PendingDuels))
    for each in PendingDuels:
        if (time.time() - each['timeRequested']) >= 120:
            PendingDuels.remove(each)
            Parent.Log('Duel Script Pending Removed', str(PendingDuels))
    Parent.Log('Duel Script Checks Finished', 'Finished')
    return


# ---------------------------
#   [Optional] Parse method (Allows you to create your own custom $parameters)
# ---------------------------


def Parse(parseString, userid, username, targetid, targetname, message):
    if "$myparameter" in parseString:
        return parseString.replace("$myparameter", "I am a cat!")

    return parseString


# ---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
# ---------------------------


def ReloadSettings(jsonData):
    Configuration = json.loads(jsonData)
    with open('config.json', mode='w+') as config:
        json.dump(Configuration, config)
    return


# ---------------------------
#   [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
# ---------------------------


def Unload():
    return


# ---------------------------
#   [Optional] ScriptToggled (Notifies you when a user disables your script or enables it)
# ---------------------------


def ScriptToggled(state):
    return
