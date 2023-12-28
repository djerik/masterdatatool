#import redis
#from textwrap import wrap
#import time

#AMtoSC_reqNM = ['c2', 'c1', '01', '0b', '7a', '00', '00', '6c', '0a', '01', '00', '00', '00', '00', '02', '02', '01', '03', '02', '00', '8a', '00']
#AMtoSC_reqNM = ['c2', 'c1', '01', '0b', 'a1', '00', '00', '6c', '0a', '01', '00', '00', '00', '00', '02', '02', '01', '03', '02', '00', 'b1', '00']
#SCtoAM_respNM = ['c1', 'c2', '01', '14', '00', '7a', '00', '6c', '01', '08', '01', '88', '00']
#SCtoLINK_statusinfo = ['83', 'c2', '01', '14', '00', '7a', '00', '87', '1f', '04', '7a', '01', '00', '00', '1f', 'be', '01', '00', '00', '00', 'ff', '02', '01', '00', '03', '01', '01', '01', '03', '00', '02', '00', '00', '00', '00', '01', '00', '00', '00', '00', '00', 'e5', '00']
#SCtoAM_trackinfolong = ['c1', 'c2', '01', '14', '00', '00', '00', '82', '0a', '01', '06', '7a', '00', '02', '00', '00', '00', '00', '00', '01', 'a8', '00']

import redis
from textwrap import wrap
import time
import signal
import sys
import subprocess
import threading
import os
from datetime import datetime
import copy

# var we will use for storing the client address we are talking to. Default to 0x80 for "ALL" 
tgSource = "80"

def exit_handler(a, b):
    print('app terminated - sending global off')
    #r.publish('link:ml:transmit', ''.join(globalOFF))
    os._exit(0)


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

# some pre-defined answers we will later just change the recipient address   
globalOFF = ['80', 'c2', '01', '0a', '00', '00', '00', '11', '00', '01']

SCtoAM_respNR = ['c1', 'c2', '01', '14', '00', 'a1', '00', '6c', '01', '08', '01']
SCtoALL_displSRC01 = ['83', 'c2', '01', '2c', '00', 'a1', '00', '06', '11', '00', '03', '01', '01', '00', '00', '4e', '2e', '52', '41', '44', '49', '4f', '20', '20', '20', '20', '20']
SCtoALL_statusInfo02 = ['83', 'c2', '01', '14', '00', 'a1', '00', '87', '1a', '04', 'a1', '01', '00', '00', '1f', 'be', '01', '00', '00', '00', 'ff', '02', '01', '00', '03', '01', '01', '01', '03', '00', '02', '00', '00', '00', '00', '01']
SCtoAM_trackinfolong03 = ['c1', 'c2', '01', '14', '00', '00', '00', '82', '0a', '01', '06', 'a1', '00', '02', '00', '00', '00', '00', '00', '01']
SCtoALL_displSRC02 = ['83', 'c2', '01', '2c', '00', 'a1', '00', '06', '11', '00', '03', '01', '01', '00', '00', '4e', '2e', '52', '41', '44', '49', '4f', '20', '20', '20', '20', '20']
SCtoALL_exInfo01 = ['83', 'c2', '01', '2c', '00', 'a1', '00', '0b', '15', '00', '04', '00', '03', '01', 'a1', '00', '00', '00', '03', 'e7', '00', '01', '00', '01', '41', '69', '72', '50', '6c', '61', '79' ] # "AirPlay"
SCtoALL_exInfo01_raw = ['83', 'c2', '01', '2c', '00', 'a1', '00', '0b', '15', '00', '04', '00', '03', '01', 'a1', '00', '00', '00', '03', 'e7', '00', '01', '00', '01']
SCtoALL_exInfo02 = ['83', 'c2', '01', '2c', '00', 'a1', '00', '0b', '0e', '00', '02', '00', '03', '01', 'a1', '00', '00', '00', '03', 'e7', '00', '01', '00', '00']
SCtoALL_exInfo03 =     ['83', 'c2', '01', '2c', '00', 'a1', '00', '0b', '1c', '00', '03', '00', '03', '01', 'a1', '00', '00', '00', '03', 'e7', '00', '01', '00', '01', '4d', '61', '73', '74', '65', '72', '44', '61', '74', '61', '54', '6f', '6f', '6c' ] # "MasterDataTool"
SCtoALL_exInfo03_raw = ['83', 'c2', '01', '2c', '00', 'a1', '00', '0b', '1c', '00', '03', '00', '03', '01', 'a1', '00', '00', '00', '03', 'e7', '00', '01', '00', '01']

SCtoAM_NRadio = ['c1', 'c0', '01', '0a', '00', '00', '00', '20', '05', '02', '00', '01', '00', '6f', '93']
SCtoVM_NRadio = ['c0', 'c1', '01', '0a', '00', '47', '00', '20', '05', '02', '00', '01', 'ff', 'ff', '93']

# some hardcoded dbus commands for controlling shairport-sync
osNEXTcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Next"
osPREVcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Previous"
osRELEASEcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Pause"
osPLAYcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Play"

def radioWake():
    global tgSource
    # we are sending a global remote command for the "N.Radio" button
    #AMtoBL_Radio[0] = tgSource
    #AMtoBL_Radio[0] = "80"
    print("AM to BL - start radio!")
    r.publish('link:ml:transmit', ''.join(SCtoAM_NRadio))

    # when we are in a VM -> AM -> SC setup we also need to send it to VM
    time.sleep(0.5)
    r.publish('link:ml:transmit', ''.join(SCtoVM_NRadio))


def handleAudio():
    # check every second if the alsa output is open 
    # if so - switch on the node via the timer command
    # interface hardcoded to hw:0,0 - change if required
    global tgSource

    # one second initial delay
    time.sleep(1)

    RUNNING = False
    while True:
        try:
            result = subprocess.run(['cat', '/proc/asound/card0/pcm0p/sub0/status'], capture_output=True, text=True, check=True)
            output = result.stdout
            if "RUNNING" in output:
                if RUNNING == False:
                    RUNNING = True

                    # node was off and we will enable it now by using the timer wake function 
                    # timerWake()

                    # alternatively we can send a remote key for switching on 
                    radioWake()

                    # if we want we could also send commands for regulating the initial volume on the node if desired
                    # for this we are sending virtual remote keys
                    # following loop will send 15 "volume_up" commands - volume step size = two
                    # but first we have to wait a bit until the node switched on properly
                    time.sleep(6)

                    #AMtoBL_volUp[0] = tgSource
                    #for i in range(15):
                        #print("vol + 1")
                        #r.publish('link:ml:transmit', ''.join(AMtoBL_volUp))
                        # wait a bit until the message was transmitted sucessfully
                        #time.sleep(0.4)
            else:
                if RUNNING == True:
                    RUNNING = False
                    print("CLOSED - global off")
                    r.publish('link:ml:transmit', ''.join(globalOFF))
                    # sometimes we need to send it twice to be sure
                    time.sleep(1)
                    r.publish('link:ml:transmit', ''.join(globalOFF))
        except subprocess.CalledProcessError as e:
            print(f"Error executing 'cat': {e}")
            return None
        time.sleep(1)


def updateStatusName(name):
    name = name.replace(" ", "")
    hex_values = [hex(ord(char))[2:] for char in name]
    nameUdateCmd = copy.copy(SCtoALL_exInfo01_raw)
    for byte in hex_values:
        nameUdateCmd.append(byte)
    nameUdateCmd[8] = hex(len(hex_values) + 14)[2:]
    print(nameUdateCmd)
    r.publish('link:ml:transmit', ''.join(nameUdateCmd))

def updateCountryName(name):
    name = name.replace(" ", "")
    hex_values = [hex(ord(char))[2:] for char in name]
    nameUdateCmd = copy.copy(SCtoALL_exInfo03_raw)
    for byte in hex_values:
        nameUdateCmd.append(byte)
    nameUdateCmd[8] = hex(len(hex_values) + 14)[2:]
    r.publish('link:ml:transmit', ''.join(nameUdateCmd))

def handleMeta():
    time.sleep(3)
    pubsub = r.pubsub()
    pubsub.subscribe('link:ml:transmit:meta:title')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data']
            datastr = data.decode("utf-8")
            print("META: " + datastr )
            #r.publish('link:ml:transmit', ''.join((SCtoALL_displSRC02)))
            #time.sleep(0.5)
            updateStatusName(datastr)
            #time.sleep(0.5)
            #r.publish('link:ml:transmit', ''.join((SCtoALL_exInfo02)))
            #time.sleep(0.5)
            #updateCountryName("MasterDataTool")

def handleTelegram(tg):

    global tgSource
    # we are simulating an AUDIO MASTER at address c1
    # is the telegram for us? If yes, proceed
    print(tg)
    if tg[0] in ["c2", "c3"]:
        # telegram to source center
        # we have to store the from address
        # so let's store the sending address and use it for any response
        tgSource = tg[1]

        if tg[3] == "0b":
            # telegram is a request

            if tg[7] == "6c":
                # telegram is a request for a source center souce
                # we have to find out which source send an answer to the requesting node
                if tg[4] == "7a":
                    # telegram is a request for N.RADIO from source center
                    #AMtoBL_respLMcmd[0] = tgSource
                    print("telegram is a request for N.RADIO from source center - send an answer")
                    #r.publish('link:ml:transmit', ''.join((AMtoBL_respLMcmd)))
                if tg[4] == "a1":
                    # telegram is a request for N.MUSIC from source center
                    print("telegram is a request for N.MUSIC from source center - send an answer")
                    r.publish('link:ml:transmit', ''.join((SCtoAM_respNR)))
                    time.sleep(0.5)
                    r.publish('link:ml:transmit', ''.join((SCtoALL_displSRC01)))
                    time.sleep(0.5)
                    r.publish('link:ml:transmit', ''.join((SCtoALL_statusInfo02)))
                    time.sleep(0.5)
                    r.publish('link:ml:transmit', ''.join((SCtoAM_trackinfolong03)))
                    time.sleep(0.5)
                    r.publish('link:ml:transmit', ''.join((SCtoALL_displSRC02)))
                    time.sleep(0.5)
                    updateStatusName("Connecting")
                    time.sleep(0.5)
                    r.publish('link:ml:transmit', ''.join((SCtoALL_exInfo02)))
                    time.sleep(0.5)
                    updateCountryName("MasterDataTool")

            if tg[7] == "45":
                # telegram is a request for a GOTO-SOURCE command

                if tg[11] == "6f":
                    # node is requesting RADIO source
                    # first we have to send an broadcast answer
                    print("telegram is a RADIO request - send an answer")
                    #r.publish('link:ml:transmit', ''.join((AMtoALL_respGotoRadio)))
                    time.sleep(1)
                    # now we have to send an answer to the requesting node
                    #AMtoBL_respGotoRadio[0] = tgSource
                    #r.publish('link:ml:transmit', ''.join((AMtoBL_respGotoRadio)))
                    time.sleep(1)
                    # finally we also have to send the new track / station info to the requesting node
                    #AMtoBL_respTrackInfoLongRadio[0] = tgSource
                    #r.publish('link:ml:transmit', ''.join((AMtoBL_respTrackInfoLongRadio)))
                    # let's start our playback
                    print("PLAY")
                    os.system(osPLAYcmd)

                if tg[11] == "8d":
                    # node is requesting CD source
                    # first we have to send an broadcast answer
                    print("telegram is a CD request - send an answer")
                    #r.publish('link:ml:transmit', ''.join((AMtoALL_respGotoCd)))
                    time.sleep(1)
                    # now we have to send an answer to the requesting node
                    #AMtoBL_respGotoCd[0] = tgSource
                    #r.publish('link:ml:transmit', ''.join((AMtoBL_respGotoCd)))
                    time.sleep(1)
                    # finally we also have to send the new track / station info to the requesting node
                    # node will then start playback
                    #AMtoBL_respTrackInfoLongCd[0] = tgSource
                    #r.publish('link:ml:transmit', ''.join((AMtoBL_respTrackInfoLongCd)))


        if tg[3] == "14":
            # tg is a response
            if tg[7] == "3c":
                # tg is a timer response
                # let's just assume we sent a timer request before and the node now told us it has the timer enabled
                # we are now sending an activate command that will turn on the node
                print("telegram is a timer response - send an answer")
                #AMtoBL_resptimerPlayRadio[0] = tgSource
                #r.publish('link:ml:transmit', ''.join(AMtoBL_resptimerPlayRadio))

        if tg[3] == "0a":
            # tg is a command
            if tg[7] == "0d":
                # tg is a virtual remote button event we can use for controlling our audio player application
                if tg[11] == "1e":
                    # NEXT
                    print("NEXT")
                    os.system(osNEXTcmd)
                if tg[11] == "1f":
                    # PREVIOUS
                    print("PREV")
                    os.system(osPREVcmd)
            if tg[7] == "11":
                # RELEASE command usually sent when node is shutting down
                print("RELEASE")
                os.system(osRELEASEcmd)


# Connect to our ML telegram broker over redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Subscribe to the receive channel
pubsub = r.pubsub()
pubsub.subscribe('link:ml:receive')

# once we detect that our system plays an audio stream we are going to send a timer "playback started" command to enable the node.
audio_thread = threading.Thread(target=handleAudio)
audio_thread.start()

# once we detect that our system plays an audio stream we are going to send a timer "playback started" command to enable the node.
meta1_thread = threading.Thread(target=handleMeta)
meta1_thread.start()

# set gpios to output (super ugly, better use libgpiod for portability)
os.system("raspi-gpio set 23 op")
os.system("raspi-gpio set 25 op")

# gpio 23 is ML POWER enable
os.system("raspi-gpio set 23 dl")
# gpio 25 is master/slave select. setting this low provides +/- 0.25V to the data pins
os.system("raspi-gpio set 25 dh")

for message in pubsub.listen():
    if message['type'] == 'message':
        data = message['data']
        datastr = data.decode("utf-8")
        datalist = wrap(datastr, 2)
        handleTelegram(datalist)
        # Process the received data