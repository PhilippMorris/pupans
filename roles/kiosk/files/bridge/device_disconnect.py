import threading
import time
import json
from adb import ADB
from sender import Sender


class CheckDevice(object):

    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        adb1 = ADB()
        sender = Sender()
        while True:
            if "{}" not in str(adb1.get_devices()):
                pass
            else:
                try:
                    sender.send("android-remove", json.loads("{}"))
                    print "Android remove event was sent"
                except Exception as e:
                    print e
                return
            time.sleep(self.interval)