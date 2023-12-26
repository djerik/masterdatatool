

class TgReceive:
    def sourceStatusInfo(self, tg):
        tgFrom = tg[0]
        tgTo = tg[1]
        tgType = tg[3]
        tgSrcDest = tg[4]
        tgOrigSrc = tg[5]
        tgPlLen = tg[8]
        print(f"Handling Type 1 with hex string: {tg}")

    def command(self, tg):
        print(f"Handling Type 2 with hex string: {tg}")

    def trackInfoLong(self, tg):
        print(f"Handling Type 3 with hex string: {tg}")

    def goToSource(self, tg):
        print(f"Unhandled type with hex string: {tg}")

    def lockmanagerKey(self, tg):
        print(f"Unhandled type with hex string: {tg}")

    def virtualRemoteKey(self, tg):
        print(f"Unhandled type with hex string: {tg}")

    def mlgwStatus(self, tg):
        print("VOLUME: " + str(int(tg[12], 16)))

    def masterHandler(self, tg):
        print(f"Unhandled type with hex string: {tg}")
        
    def clock(self, tg):
        print("TIME: " + tg[13] + ":" + tg[14])
        print("DATE: " + tg[17] + "." + tg[18] + "." + tg[19])