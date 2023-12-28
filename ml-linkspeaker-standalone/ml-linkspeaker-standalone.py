import redis
from textwrap import wrap
import time
import signal
import sys
import subprocess
import threading
import os
from datetime import datetime

# var we will use for storing the client address we are talking to. Default to 0x80 for "ALL" 
tgSource = "80"

def exit_handler(a, b):
    print('app terminated - sending global off')
    r.publish('link:ml:transmit', ''.join(globalOFF))
    os._exit(0)


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

# some pre-defined answers we will later just change the recipient address   
globalOFF = ['80', '05', '01', '0a', '00', '00', '00', '11', '00', '01']
AMtoBL_respAM = ['06', 'c1', '01', '14', '00', '00', '00', '04', '03', '04', '01', '02', '01']
AMtoBL_respDistSrc = ['06', 'c1', '01', '14', '00', '00', '00', '08', '00', '04']
AMtoBL_respLocalSrc = ['06', 'c1', '01', '14', '00', '00', '00', '30', '00', '04']
AMtoBL_respLMcmd = ['06', 'c0', '01', '14', '00', '00', '00', '5c', '01', '02', '01']
AMtoALL_respGotoRadio = ['83', 'c1', '01', '14', '00', '6f', '00', '87', '15', '04', '6f', '01', '00', '00', '00', '7e', '01', '01', '00', '01', '01', '02', '01', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff']
AMtoALL_respGotoCd = ['83', 'c1', '01', '14', '00', '8d', '00', '87', '15', '04', '8d', '01', '00', '00', '00', '7e', '01', '01', '00', '01', '01', '02', '01', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff', 'ff']
AMtoBL_respGotoRadio = ['06', 'c1', '01', '14', '00', '00', '00', '44', '0b', '05', '02', '6f', '00', '02', '01', '00', '01', '00', '00', '00', 'ff']
AMtoBL_respGotoCd = ['06', 'c1', '01', '14', '00', '00', '00', '44', '0b', '05', '02', '8d', '00', '02', '01', '00', '01', '00', '00', '00', 'ff']
AMtoBL_respTrackInfoLongRadio = ['06', 'c1', '01', '14', '00', '00', '00', '82', '0a', '01', '06', '6f', '01', '02', '01', '00', '00', 'ff', 'ff', '01']
AMtoBL_respTrackInfoLongCd = ['06', 'c1', '01', '14', '00', '00', '00', '82', '0a', '01', '06', '8d', '01', '02', '01', '00', '00', 'ff', 'ff', '01']
AMtoBL_respClock = ['80', 'c1', '01', '14', '00', '00', '00', '40', '0b', '0b', '0a', '00', '03', '11', '52', '59', '00', '23', '12', '23', '0a']
AMtoALL_reqtimer = ['80', 'c1', '01', '0a', '00', '00', '00', '3c', '07', '0f', '00', '0a', '12', '05', '23', '12', '23']
AMtoBL_resptimerPlayRadio = ['06', 'c1', '01', '0a', '00', '00', '00', '3c', '05', '02', '00', '01', '01', '6f', '01']
AMtoBL_volUp = ['06', 'c1', '01', '0a', '00', '00', '00', '20', '05', '02', '00', '01', '00', '6f', '60']
AMtoBL_volDown = ['06', 'c1', '01', '0a', '00', '00', '00', '20', '05', '02', '00', '01', '00', '6f', '64']
AMtoBL_Radio = ['06', 'c1', '01', '0a', '00', '00', '00', '20', '05', '02', '00', '01', '00', '6f', '81']

# some hardcoded dbus commands for controlling shairport-sync
osNEXTcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Next"
osPREVcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Previous"
osRELEASEcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Pause"
osPLAYcmd = "dbus-send --system --print-reply --type=method_call --dest=org.gnome.ShairportSync '/org/gnome/ShairportSync' org.gnome.ShairportSync.RemoteControl.Play"

def radioWake():
    global tgSource
    # we are sending a global remote command for the "Radio" button
    AMtoBL_Radio[0] = tgSource
    AMtoBL_Radio[0] = "80"
    print("AM to BL - start radio!")
    r.publish('link:ml:transmit', ''.join(AMtoBL_Radio))

def timerWake():
    # we are requesting timer info from all nodes
    # if a node has its timer enabled it will make a response
    print("AM to ALL - timer remote start!")
    r.publish('link:ml:transmit', ''.join(AMtoALL_reqtimer))

def clockOneshot():
    # b13 = hh / b14 = mm / b15 = ss 
    # b17 = dd / b18 = mm / b19 = yy
    current_datetime = datetime.now()
    current_hour = current_datetime.strftime('%H')
    current_minute = current_datetime.strftime('%M')
    current_second = current_datetime.strftime('%S')
    current_day = current_datetime.strftime('%d')
    current_month = current_datetime.strftime('%m')
    current_year = current_datetime.strftime('%y')

    AMtoBL_respClock[13] = current_hour
    AMtoBL_respClock[14] = current_minute
    AMtoBL_respClock[15] = current_second

    AMtoBL_respClock[17] = current_day
    AMtoBL_respClock[18] = current_month
    AMtoBL_respClock[19] = current_year

    print("CLOCK SYNC")

    r.publish('link:ml:transmit', ''.join(AMtoBL_respClock))

def syncClock():
    # running in a thread
    while True:
        clockOneshot()
        # sync the time every 30 minutes
        time.sleep(1800)


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

                    AMtoBL_volUp[0] = tgSource
                    for i in range(15):
                        print("vol + 1")
                        r.publish('link:ml:transmit', ''.join(AMtoBL_volUp))
                        # wait a bit until the message was transmitted sucessfully
                        time.sleep(0.4)
            else:
                if RUNNING == True:
                    RUNNING = False
                    print("CLOSED - global off")
                    r.publish('link:ml:transmit', ''.join(globalOFF))
        except subprocess.CalledProcessError as e:
            print(f"Error executing 'cat': {e}")
            return None
        time.sleep(1)




def handleTelegram(tg):

    global tgSource
    # we are simulating an AUDIO MASTER at address c1
    # is the telegram for us? If yes, proceed
    print(tg)
    if tg[0] in ["c1", "80"]:
        # telegram to audio master
        # we have to store the from address
        # 03 = BL3500 / 06 = BL2000 / probably nodes can also be assigned a new address
        # so let's store the sending address and use it for any response
        tgSource = tg[1]

        if tg[3] == "0b":
            # telegram is a request

            if tg[7] == "04":
                # telegram is a master request
                # we have to send an answer to the requesting node
                print("telegram is a master request - send an answer")
                AMtoBL_respAM[0] = tgSource
                r.publish('link:ml:transmit', ''.join(AMtoBL_respAM))

            if tg[7] == "08":
                # telegram is a request for the currently distributed source
                # we have to send an answer to the requesting node
                print("telegram is a distributed source request - send an answer")
                AMtoBL_respDistSrc[0] = tgSource
                r.publish('link:ml:transmit', ''.join(AMtoBL_respDistSrc))

            if tg[7] == "30":
                # telegram is a request for the currently local source in use
                # we have to send an answer to the requesting node
                print("telegram is a local source request - send an answer")
                AMtoBL_respLocalSrc[0] = tgSource
                r.publish('link:ml:transmit', ''.join(AMtoBL_respLocalSrc))

            if tg[7] == "5c":
                # telegram is a request for a lockmanager key
                # we have to send an answer to the requesting node
                print("telegram is a lockmanager key request - send an answer")
                AMtoBL_respLMcmd[0] = tgSource
                r.publish('link:ml:transmit', ''.join((AMtoBL_respLMcmd)))

            if tg[7] == "45":
                # telegram is a request for a GOTO-SOURCE command

                if tg[11] == "6f":
                    # node is requesting RADIO source
                    # first we have to send an broadcast answer
                    print("telegram is a RADIO request - send an answer")
                    r.publish('link:ml:transmit', ''.join((AMtoALL_respGotoRadio)))
                    time.sleep(1)
                    # now we have to send an answer to the requesting node
                    AMtoBL_respGotoRadio[0] = tgSource
                    r.publish('link:ml:transmit', ''.join((AMtoBL_respGotoRadio)))
                    time.sleep(1)
                    # finally we also have to send the new track / station info to the requesting node
                    AMtoBL_respTrackInfoLongRadio[0] = tgSource
                    r.publish('link:ml:transmit', ''.join((AMtoBL_respTrackInfoLongRadio)))
                    # let's start our playback
                    print("PLAY")
                    os.system(osPLAYcmd)

                if tg[11] == "8d":
                    # node is requesting CD source
                    # first we have to send an broadcast answer
                    print("telegram is a CD request - send an answer")
                    r.publish('link:ml:transmit', ''.join((AMtoALL_respGotoCd)))
                    time.sleep(1)
                    # now we have to send an answer to the requesting node
                    AMtoBL_respGotoCd[0] = tgSource
                    r.publish('link:ml:transmit', ''.join((AMtoBL_respGotoCd)))
                    time.sleep(1)
                    # finally we also have to send the new track / station info to the requesting node
                    # node will then start playback
                    AMtoBL_respTrackInfoLongCd[0] = tgSource
                    r.publish('link:ml:transmit', ''.join((AMtoBL_respTrackInfoLongCd)))

                if tg[7] == "40":
                    # telegram is a request for a clock sync
                    # send a sync response
                    clockOneshot()


        if tg[3] == "14":
            # tg is a response
            if tg[7] == "3c":
                # tg is a timer response
                # let's just assume we sent a timer request before and the node now told us it has the timer enabled
                # we are now sending an activate command that will turn on the node
                print("telegram is a timer response - send an answer")
                AMtoBL_resptimerPlayRadio[0] = tgSource
                r.publish('link:ml:transmit', ''.join(AMtoBL_resptimerPlayRadio))

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

# every 30 minutes are going to sync the clock of all connected nodes
clock_thread = threading.Thread(target=syncClock)
clock_thread.start()

# set gpios to output (super ugly, better use libgpiod for portability)
os.system("raspi-gpio set 23 op")
os.system("raspi-gpio set 25 op")

# gpio 23 is ML POWER enable
os.system("raspi-gpio set 23 dh")
# gpio 25 is master/slave select. setting this low provides +/- 0.25V to the data pins
os.system("raspi-gpio set 25 dl")

time.sleep(1)

for message in pubsub.listen():
    if message['type'] == 'message':
        data = message['data']
        datastr = data.decode("utf-8")
        datalist = wrap(datastr, 2)
        handleTelegram(datalist)
        # Process the received data