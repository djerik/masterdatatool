from pickle import FALSE
import serial
import threading
import queue
import time
import redis
from textwrap import wrap

r = redis.StrictRedis(host='localhost', port=6379, db=0)

ser = serial.Serial('/dev/ttyUSB0', parity=serial.PARITY_ODD, timeout=0.04)
ser.baudrate = 19200
ser.close()
ser.open()

wd_cancle_flag = False
wd_start_flag = False
sending = False
last_sent_telegram = ""


ml_src_type_list = ['c0', 'c1', 'c2', '80', '81', '82', '83', 'f0']


def send_raw_hex_data_mark(port, baudrate, hex_data):
    global ser
    ser.close()
    ser.open()
    ser.parity = serial.PARITY_MARK

    data_bytes = bytes.fromhex(hex_data)
    ser.write(data_bytes)

def send_raw_hex_data_space(port, baudrate, hex_data):
    global ser
    ser.close()
    ser.open()
    ser.parity = serial.PARITY_SPACE

    data_bytes = bytes.fromhex(hex_data)
    ser.write(data_bytes)

def sendcmd(cmd):
    global ser

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

    i=0
    for data in cmd:
        if i == 0:
            precmd = cmd[i]
        else:
            maincmd = maincmd + cmd[i]
        i = i+1

    print("SENDING:")
    print(precmd + maincmd + "00" )
    last_sent_telegram = precmd + maincmd + "00"
    print("")

    send_raw_hex_data_mark('/dev/ttyUSB0', 19200, precmd)
    send_raw_hex_data_space('/dev/ttyUSB0', 19200, maincmd)
    send_raw_hex_data_mark('/dev/ttyUSB0', 19200, '00')

def checkSend(data_queue, send_queue):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('link:ml:transmit')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data']
            datastr = data.decode("utf-8")
            send_queue.put(datastr)


def mlDataWatchdog():
    global wd_cancle_flag
    global wd_start_flag

    while True:
        time.sleep(0.1)
        if wd_start_flag == True:
            time.sleep(1)
            if wd_cancle_flag == False:
                wd_cancle_flag = True
                print("TELEGRAM TIMEOUT")


def telegram_decoder(receive_queue, incoming_data_event):

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    # global watchdog_cancle flag
    global wd_cancle_flag

    # global watchdog_start flag
    global wd_start_flag
    
    # list for storing our incoming telegram data
    telegram = []

    # each telegram contains a byte letting us know how long the payload will be
    payload_length = 0

    # flag that will stop the main loop
    # will be set one an invalid telegram was detected
    stop_decode = False

    while True:
        incoming_data_event.wait()

        if wd_cancle_flag:
            # got a timeout from our watchdog
            telegram = []

        else:
            # keep decoding
            new_telegram_byte = receive_queue.get()
            telegram.append(new_telegram_byte)
            telegram_length = len(telegram)
            stop_decode = False

            if telegram_length == 1 and not stop_decode:
                if telegram[0] == "00":
                    # firt byte in telegram cannot be 00
                    # no valid start - ignoring and deleting
                    telegram = []
                    stop_decode = True

            if telegram_length == 2 and not stop_decode:
                # byte 0 & 1 are the TO / FROM addresses
                # check if they are valid
                # ignore and delete telegram list otherwise
                # one address is always known, the other is dynamic
                # let's store the comparisong result in two lags for later comparison
                byte0_valid = False
                byte1_valid = False

                if telegram[0] in ml_src_type_list:
                    # byte 0 is a valid ML address
                    byte0_valid = True
                if telegram[1] in ml_src_type_list:
                    # byte 0 is a valid ML address
                    byte1_valid = True

                # now check if the telegram has a valid start
                # if not, ignore and delete it
                if byte0_valid or byte1_valid:
                    # telegram has a valid start
                    # to prevent a lock-up situation we are now starting our watchdog
                    # the watchdog will 
                    wd_start_flag = True
                else:
                    # telegram does not have a valid start
                    # ignore and delete it
                    telegram = []
                    stop_decode = True

            if telegram_length == 9 and not stop_decode:
                payload_length = int(telegram[8], 16)

            if telegram_length > 50 and not stop_decode:
                # usually telegrams are not that long
                # let's ignore and delete it
                telegram = []
                stop_decode = True

            if telegram_length > 9 and not stop_decode:
                # looking like we got a valid telegram
                # keep adding to the telegram list
                # stop at payload_length + 8 (header) + 1 (reserved byte) + 1 (checksum byte) + 1 (telegram end byte "00")
                calculated_telegram_length = payload_length + 8 + 1 + 1 + 1 + 1

                if telegram_length == calculated_telegram_length:
                    # telegram is complete
                    # let's check if the checksum is valid
                    chksum_string_calculated = "00"
                    chksum_int_calculated = 0

                    for byte in telegram[:-2]:
                        chksum_int_calculated = chksum_int_calculated + int(byte,16)
                        chksum_string_calculated = str(hex(chksum_int_calculated))

                        if len(chksum_string_calculated) > 2:
                            # longer checksums will just get truncated to fit into that byte
                            chksum_string_calculated = chksum_string_calculated[-2:]

                    # compare if the received checksum is valid
                    # if yes, publish on redis
                    if chksum_string_calculated == telegram[telegram_length - 2]:
                        # all good - half-duplex so we need to check if it was our message
                        telegram_string = ''.join(telegram)
                        #print(telegram_string + ":" + last_sent_telegram.lower())
                        if telegram_string != last_sent_telegram.lower():
                            print("TELEGRAM RECEIVED: ")
                            print(telegram_string)
                            r.publish('link:ml:receive', telegram_string)
                            print("")
                        
                        # clear for new telegram
                        telegram = []
                    else:
                        # checksum mismatch!
                        print("CHECKSUM MISMATCH!")
                        print(telegram)
                        print("Expected: " + chksum_string_calculated)
                        print("Received: " + telegram[telegram_length - 2])
                        print("")


def handle_serial_receive(receive_queue, send_queue, incoming_data_event):
    global ser

    # flag that gets set during sending to prevent reading at the same time (half-duplex)
    global sending

    while True:
        # keep reading
        if not sending:
            data = ser.read(1)
            if len(data.hex()) > 0:
                # new byte incoming - let's put it in the receive queue
                if not sending:
                    receive_queue.put(data.hex())
                    incoming_data_event.set()
                else:
                    print("blocked: " + data.hex())


def handle_serial_transmit(receive_queue, send_queue, incoming_data_event):
    global sending

    # flag that gets set during sending to prevent reading at the same time (half-duplex)
    sending = False

    while True:
        if not send_queue.empty():
            sending = True
            # let's give the serial interface some time for a time-out
            time.sleep(0.05)
            # something new in send_queue - let's send it
            send = send_queue.get()
            send = wrap(send, 2)
            sendcmd(send)
            # let's give the serial interface some time for a time-out
            time.sleep(0.05)
            sending = False
        time.sleep(0.2)


if __name__ == "__main__":

    receive_queue = queue.Queue()
    send_queue = queue.Queue()

    incoming_data_event = threading.Event()

    serial_receive_thread = threading.Thread(target=handle_serial_receive, args=(receive_queue, send_queue, incoming_data_event))
    serial_receive_thread.start()

    serial_transmit_thread = threading.Thread(target=handle_serial_transmit, args=(receive_queue, send_queue, incoming_data_event))
    serial_transmit_thread.start()

    telegram_thread = threading.Thread(target=telegram_decoder, args=(receive_queue, incoming_data_event))
    telegram_thread.start()

    redis_send_thread = threading.Thread(target=checkSend, args=(receive_queue, send_queue))
    redis_send_thread.start()

