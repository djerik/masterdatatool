from mlTelegramRx import TgReceive
import redis
from textwrap import wrap


def handleTelegram(tg):

    telegram_types = {
    "87": "sourceStatusInfo",
    "0d": "command",
    "82": "trackInfoLong",
    "45": "goToSource",
    "44": "trackChangeInfo",
    "5c": "lockmanagerKey",
    "20": "virtualRemoteKey",
    "98": "mlgwStatus",
    "04": "masterHandler",
    "40": "clock",

}
    tgPlType = tg[7]
    tgRxMethode = telegram_types.get(tgPlType, None)
    handler = TgReceive()

    if tgRxMethode:
        handler_function = getattr(handler, tgRxMethode)
        handler_function(tg)
    else:
        print(f"NOT IMPLEMENTED: {tgPlType}")


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
