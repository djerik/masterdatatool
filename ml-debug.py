from pickle import FALSE
import serial
import threading
import queue
import binascii
import sys
import signal
import os
import redis
from textwrap import wrap

from const import *

'''
ser = serial.Serial('/dev/ttyUSB0', parity=serial.PARITY_ODD)

ser.baudrate = 19200
ser.close()
ser.baudrate = 19200
ser.open()
ser.ReadBufferSize = 32768
'''
#ser = serial.Serial('/dev/ttymxc2', 19200, parity=serial.PARITY_NONE)
#ser.close()
#ser.open()
#ser.baudrate = 19200
#ser.reset_output_buffer()

#ser.close()
#ser.baudrate = 19200
#ser.open()
#ser.ReadBufferSize = 32768

telegram = []
chksum = 0
lastchksum = ""
chktxt = ""
readEOT = False
exitf = False

def _dictsanitize(d, s):
    result = d.get(s)
    if result is None:
        result = "UNKNOWN (type=" + _hexbyte(s) + ")"
    return str(result)

def _hexbyte(byte):
    resultstr = hex(byte)
    if byte < 16:
        resultstr = resultstr[:2] + "0" + resultstr[2]
    return resultstr


def _hexword(byte1, byte2):
    resultstr = _hexbyte(byte2)
    resultstr = _hexbyte(byte1) + resultstr[2:]
    return resultstr

def lookupSourceDest(input):
    if input == "c0":
        return ("VIDEO MASTER")
    elif input == "c1":
        return ("AUDIO MASTER")
    elif input == "c2":
        return ("SOURCE CENTER")
    elif input == "81":
        return ("ALL AUDIO LINK")
    elif input == "82":
        return ("ALL VIDEO LINK")
    elif input == "83":
        return ("ALL LINK")
    elif input == "80":
        return ("ALL DEVICES")
    elif input == "f0":
        return ("MLGW")
    else:
        return ("UNKNOWN")
    


def printTelegram():
    global telegram
    print("##########################################")
    print("##########################################")
    print("##########################################")
    print("NEW TELEGRAM:")
    print(telegram)
    decodeTelegram(telegram)
    telegram = []
    print("")


def decodeTelegram(telegram):
    print("------------------------------------------")
    print("--- HEADER ---")
    print("------------------------------------------")
    i = 0
    for byte in telegram:
        if i == 0:
            print("TO:\t\t" + telegram[i] + " \t " + _dictsanitize(ml_src_type_dict, int(telegram[i], 16)))
        if i == 1:
            print("FROM:\t\t" + telegram[i] + " \t " + _dictsanitize(ml_src_type_dict, int(telegram[i], 16)))
        if i == 2:
            print("BYTE2:\t\t" + telegram[i] + " \t " + "???")
        if i == 3:
            print("TYPE:\t\t" + telegram[i] + " \t " + _dictsanitize(ml_telegram_type_dict, int(telegram[i], 16)))
        if i == 4:
            print("SRC DEST:\t" + telegram[i] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[i], 16)))
        if i == 5:
            print("ORIG SRC:\t" + telegram[i] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[i], 16)))
        if i == 6:
            print("BYTE6:\t\t" + telegram[i] + " \t " + "???")
        if i == 7:
            print("PL TYPE:\t" + telegram[i] + " \t " + _dictsanitize(ml_command_type_dict, int(telegram[i], 16)))
        if i == 8:
            print("PL LENGTH:\t" + telegram[i] + " \t " + str(int(telegram[i], 16)))
        i = i+1
    
    if telegram[7] == "87":
        # source status info
        #print(len(telegram))
        if len(telegram) < 13:
            print("TELEGRAM TOO SHORT")
        else:
            print("------------------------------------------")
            print("--- PAYLOAD ---")
            print("--- source status info ---")
            print("------------------------------------------")
            print("SOURCE:\t\t" + telegram[10] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[10], 16)))
            print("LOCAL SRC:\t" + telegram[13] + " \t " + "???")
            print("SRC MEDIUM:\t" + telegram[18] + " " + telegram[17] + " \t " + "???")
            print("CH TRACK:\t" + "NA" + " \t " + str(int(telegram[19], 16)) if int(telegram[8], 16) < 27 else (str(int(telegram[36], 16) * 256 + int(telegram[37], 16))))
            print("ACTIVITY:\t" + telegram[21] + " \t " + _dictsanitize(ml_state_dict, int(telegram[21])))
            print("SOURCE TYPE:\t" + telegram[22] + " \t " + "???")
            print("PICTURE IDENT:\t" + telegram[22] + " \t " + _dictsanitize(ml_pictureformatdict, int(telegram[21])))

    if telegram[7] == "0d":
        # beo4 command
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- beo4 command ---")
        print("------------------------------------------")
        print("SOURCE:\t\t" + telegram[10] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[10], 16)))
        print("BEO4 BUTTON:\t" + telegram[11] + " \t " + _dictsanitize(beo4_commanddict, int(telegram[11], 16)))

    if telegram[7] == "82":
        # track info long
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- track info long ---")
        print("------------------------------------------")
        print("SOURCE:\t\t" + telegram[11] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[11], 16)))
        print("CH TRACK:\t" + telegram[12] + " \t " + str(int(telegram[12], 16)))
        print("ACTIVITY:\t" + telegram[13] + " \t " + _dictsanitize(ml_state_dict, int(telegram[13], 16)))

    if telegram[7] == "45":
        # go to source
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- go to source ---")
        print("------------------------------------------")
        print("SOURCE:\t\t" + telegram[11] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[11], 16)))
        print("CH TRACK:\t" + telegram[12] + " \t " + str(int(telegram[12], 16)))

    if telegram[7] == "44":
        # track change info 
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- track change info ---")
        print("------------------------------------------")
        if telegram[9] == "07":
            print("TYPE:\t\t" + telegram[9] + " \t " + "CHANGE_SOURCE")
            print("PREV SOURCE:\t" + telegram[11] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[11], 16)))
            print("NEW SOURCE:\t" + telegram[22] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[22], 16)))
        elif telegram[9] == "05":
            print("TYPE:\t\t" + telegram[9] + " \t " + "CURRENT_SOURCE")
            print("CURR SOURCE:\t" + telegram[11] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[11], 16)))
        elif telegram[9] == "09":
            print("TYPE:\t\t" + telegram[9] + " \t " + "SOURCE_NOT_AVAILABLE")
            print("REQ SOURCE:\t" + telegram[11] + " \t " + _dictsanitize(ml_selectedsourcedict, int(telegram[11], 16)))
        else:
            print("TYPE:\t\t" + telegram[9] + " \t " + "UNKNOWN")

    if telegram[7] == "5c":
        # lockmanager request key
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- lockmanager request key ---")
        print("------------------------------------------")
        if telegram[9] == "01":
            print("TYPE:\t\t" + telegram[9] + " \t " + "REQUEST_KEY")
        elif telegram[9] == "02":
            print("TYPE:\t\t" + telegram[9] + " \t " + "TRANSFER_KEY")
            print("KEY:\t\t" + telegram[10] + " \t " + "KEY")
        elif telegram[9] == "04":
            print("TYPE:\t\t" + telegram[9] + " \t " + "KEY_RECEIVED")
            print("KEY:\t\t" + telegram[10] + " \t " + "KEY")
        elif telegram[9] == "05":
            print("TYPE:\t\t" + telegram[9] + " \t " + "TIMEOUT")
        else:
            print("TYPE:\t\t" + telegram[9] + " \t " + "UNDEFINED")

    if telegram[7] == "20":
        # virtual beo4 key
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- virtual beo4 key ---")
        print("------------------------------------------")
        print("COMMAND:\t" + telegram[14] + " \t " + _dictsanitize(beo4_commanddict, int(telegram[14], 16)))
        print("DEST SELECT:\t" + telegram[11] + " \t " + _dictsanitize(ml_destselectordict, int(telegram[11], 16)))

    if telegram[7] == "98":
        # mlgw status broadcast
        print("------------------------------------------")
        print("--- PAYLOAD ---")
        print("--- mlgw status broadcast ---")
        print("------------------------------------------")
        print("MUTE STATUS :\t" + telegram[10] + " \t ")
        print("VOLUME (hex) :\t" + telegram[12] + " \t " + str(int(telegram[12], 16)) + " (int)")
        




    print("##########################################")
    print("##########################################")
    print("##########################################")
    print("")



tgheader = False


# Connect to Redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Subscribe to a channel
pubsub = r.pubsub()
pubsub.subscribe('beolink:ml:receive')

for message in pubsub.listen():
    if message['type'] == 'message':
        data = message['data']
        datastr = data.decode("utf-8")
        datalist = wrap(datastr, 2)
        telegram = datalist
        printTelegram()
        # Process the received data