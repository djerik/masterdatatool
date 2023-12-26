import redis
from textwrap import wrap
import time

#AMtoSC_reqNM = ['c2', 'c1', '01', '0b', '7a', '00', '00', '6c', '0a', '01', '00', '00', '00', '00', '02', '02', '01', '03', '02', '00', '8a', '00']
AMtoSC_reqNM = ['c2', 'c1', '01', '0b', 'a1', '00', '00', '6c', '0a', '01', '00', '00', '00', '00', '02', '02', '01', '03', '02', '00', 'b1', '00']
SCtoAM_respNM = ['c1', 'c2', '01', '14', '00', '7a', '00', '6c', '01', '08', '01', '88', '00']
SCtoLINK_statusinfo = ['83', 'c2', '01', '14', '00', '7a', '00', '87', '1f', '04', '7a', '01', '00', '00', '1f', 'be', '01', '00', '00', '00', 'ff', '02', '01', '00', '03', '01', '01', '01', '03', '00', '02', '00', '00', '00', '00', '01', '00', '00', '00', '00', '00', 'e5', '00']
SCtoAM_trackinfolong = ['c1', 'c2', '01', '14', '00', '00', '00', '82', '0a', '01', '06', '7a', '00', '02', '00', '00', '00', '00', '00', '01', 'a8', '00']

def handleTelegram(tg):
    global SCtoAM_respNM
    if tg == AMtoSC_reqNM:
        # AUDIO MASTER to SOURCE CENTER // req distri N.Music
        print("N.Music request from AM - sending SC answer")
        r.publish('beolink:ml:transmit', ''.join(SCtoAM_respNM))
        time.sleep(0.25)
        print("Sending dummy SC info to all link nodes")
        r.publish('beolink:ml:transmit', ''.join(SCtoLINK_statusinfo))
        time.sleep(0.25)
        print("Sending dummy SC track info long to AM")
        r.publish('beolink:ml:transmit', ''.join(SCtoAM_trackinfolong))

	


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
        handleTelegram(datalist)
        # Process the received data