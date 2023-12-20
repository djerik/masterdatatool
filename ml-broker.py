from pickle import FALSE
import serial
import threading
import queue
import binascii
import sys
import signal
import os
import time
import redis
from textwrap import wrap

from const import *

r = redis.StrictRedis(host='localhost', port=6379, db=0)

ser = serial.Serial('/dev/ttyUSB0', parity=serial.PARITY_ODD, timeout=0.3)
ser.baudrate = 19200
ser.close()
ser.baudrate = 19200
ser.open()

telegram = []
chksum = 0
lastchksum = ""
chktxt = ""
readEOT = False
exitf = False
wdflag = False
pid = ""

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


def send_raw_hex_data_mark(port, baudrate, hex_data):
    ser = serial.Serial(port, baudrate, parity=serial.PARITY_MARK)
    ser.baudrate = 19200
    ser.reset_output_buffer()

    # Convert hex string to bytes
    data_bytes = bytes.fromhex(hex_data)
    # print(data_bytes)
    # Send the data
    ser.write(data_bytes)
    # print("YES")

def send_raw_hex_data_space(port, baudrate, hex_data):
    ser = serial.Serial(port, baudrate, parity=serial.PARITY_SPACE)
    ser.baudrate = 19200
    ser.reset_output_buffer()

    # Convert hex string to bytes
    data_bytes = bytes.fromhex(hex_data)
    # print(data_bytes)
    # Send the data
    ser.write(data_bytes)
    # print("YES")

def sendcmd(cmd):
    i=0
    sum1=0
    for hex in cmd:
        sum1 = sum1 + int(cmd[i], 16)
        i = i + 1

    strHex = "%0.2X" % sum1
    if len(strHex) > 2:
        strHex = strHex[1:]

    cmd.append(strHex)

    precmd = ""
    maincmd = ""
    postcmd = ""

    i=0
    for data in cmd:
        if i == 0:
            precmd = cmd[i]
        else:
            maincmd = maincmd + cmd[i]
        i = i+1

    print(precmd + maincmd + "00" )

    send_raw_hex_data_mark('/dev/ttyUSB0', 19200, precmd)
    send_raw_hex_data_space('/dev/ttyUSB0', 19200, maincmd)
    send_raw_hex_data_mark('/dev/ttyUSB0', 19200, '00')


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
    print(''.join(telegram))
    publishTelegram(telegram)
    telegram = []
    print("")


def publishTelegram(telegram):
    print("published")
    r.publish('link:ml:receive', ''.join(telegram))




tgheader = False

def signal_handler(sig, frame):
    global exitf
    exitf = True

def read_serial(baud_rate, data_queue, send_queue):
    global exitf
    global ser
    try:
        while not exitf:
            if not send_queue.empty():
                send = send_queue.get()
                send = wrap(send, 2)
                print("SENDING")
                #print(send)
                sendcmd(send)
            else:
                data = ser.read(1)  # Adjust the number of bytes to read
                if len(data.hex()) > 1:
                    data_queue.put(data.hex())
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

def mlDataWatchdog():
    global telegram
    global chksum
    global readEOT
    global wdflag

    while True:
        time.sleep(0.1)
        if wdflag == True:
            time.sleep(1)
            if wdflag == True:
                wdflag = False
                print("TELEGRAM TIMEOUT")
                telegram = []
                chksum = 0
                readEOT = False


def process_data():
    global telegram
    global chksum
    global lastchksum
    global chktxt
    global readEOT
    global wdflag



    if len(telegram) == 1:
        if telegram[0] == "00":
            print("ignoring - 00 is no valid start")
            telegram = []
            chksum = 0
            readEOT = False
            return
    isT0 = False
    isT1 = False
    if len(telegram) == 2:
        if telegram[0] in ml_src_type_list:
            isT0 = True
        if telegram[1] in ml_src_type_list:
            isT1 = True
        if isT0 or isT1:
            print("tg start ok")
            wdflag = True
        else:
            telegram = []
            chksum = 0
            readEOT = False
            return

    if len(telegram) > 50:
        print("telegram too long - restart")
        telegram = []
        return


    #print(data)
    if readEOT == False:
        lastdata = data
        chksumhexstring = str(hex(chksum))
        #print(chksumhexstring)
        if len(chksumhexstring) > 2:
            chktxt = chksumhexstring[-2:]
            #print("chk: "+chktxt)
        
        #print("CHK INT: " + str(chksum) + " CHK HEX: " + str(hex(chksum)) + " DATA: " + data)
        if chktxt == data:
            #print("CHKSUM MATCH - EOT")
            readEOT = True

        chksum = chksum + int(data,16)

    else:
        if telegram[-1] == "00":
            wdflag = False
            printTelegram()
            chksum = 0
            readEOT = False
        else:
            telegram.append(data)
            chksum = chksum + int(data,16)
            readEOT = False

def checkSend(data_queue, send_queue):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('link:ml:transmit')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data']
            datastr = data.decode("utf-8")
            send_queue.put(datastr)
            # Process the received data


print(os.getpid())
pid = os.getpid()
exit_flag = threading.Event()
data_queue = queue.Queue()
send_queue = queue.Queue()
        
serial_thread = threading.Thread(target=read_serial, args=("19200", data_queue, send_queue))
serial_thread.start()

sendQ_thread = threading.Thread(target=checkSend, args=(data_queue, send_queue))
sendQ_thread.start()

thread = threading.Thread(target=mlDataWatchdog)

signal.signal(signal.SIGINT, signal_handler)

pubsubSend = r.pubsub()
pubsubSend.subscribe('link:ml:transmit')

while not exitf:
    if not data_queue.empty():
        data = data_queue.get()
        #print(data)
        telegram.append(data)
        process_data()

print("Program has exited.")
os.system("kill " +str(pid))
serial_thread.join()
os.kill(os.getpid(), signal.SIGINT)

