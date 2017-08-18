from adb import ADB
import subprocess
import json
from device_disconnect import CheckDevice
from sender import Sender

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return "{" + s[start:]
    except ValueError:
        return ""

def push_apk():
    print adb.run_cmd("push app-release.apk /data/local/tmp/com.basechord.aarons.androidrefresh.basechord")

def install_apk():
    print adb.run_cmd("shell pm install -r /data/local/tmp/com.basechord.aarons.androidrefresh.basechord")

def uninstall_apk():
    print adb.run_cmd("shell pm uninstall com.basechord.aarons.androidrefresh.basechord")



def start_app():
    print adb.run_cmd("shell am start -n com.basechord.aarons.androidrefresh.basechord/com.basechord.aarons.androidrefresh.basechord.app.MainActivity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER")

def parse_app_log():

    p = subprocess.Popen('adb logcat -s Aarons_Result', stdout=subprocess.PIPE, stderr=None, shell=True)
    for line in iter(p.stdout.readline, ''):

        if "beginning" not in line:
            # parse manual and auto tests counts {"auto":2,"manual":2}
            if "AppStartedCommand" in line:
                try:
                  #  print find_between(line, "{", "}")
                    sender.send("app-start", json.loads(find_between(line, "{", "}")))
                   # print find_between(line, ":{", "}")
                    print "app-start event was sent to Kiosk"
                except Exception as e:
                    print e
                    print "Can not send tests counts to Kiosk"
            elif "VipeStarted" in line:
                try:
                    sender.send("android-reset", json.loads('{}'))
                    print "Android reset event was sent to Kiosk"
                except Exception as e:
                    print e
                    print "Can not send tests counts to Kiosk"
            # parse and send to kiosk tests results.
            else:
                try:
                    print find_between(line, "{", "}")
                    sender.send("android-test", json.loads(find_between(line, "{", "}")))
                    print "Android test event was sent to Kiosk"
                except Exception as e:
                    print "Can not send test result to Kiosk"
                    print e
    p.stdout.flush()
    p.stdout.close()
    # Clear logcat buffer!!!
    adb.get_logcat(lcfilter="-c")

if __name__ == "__main__":
    print "Version 1.6"
    print "Android app v22"
    adb = ADB()
    sender = Sender()

    adb.get_logcat(lcfilter="-c")
    adb.wait_for_device()


    while True:

        while "{}" not in str(adb.get_devices()):
            # Send event "device connected" to kiosk
            try:
                sender.send("android-add", json.loads("{}"))
                print "Android add event was sent"
            except Exception as e:
                print "Can not send event to Kiosk"
                print e
            # Install BaseChord app to Android Phone
            check = CheckDevice()
            uninstall_apk()
            push_apk()
            install_apk()
            start_app()
        # Start log parser
            parse_app_log()













