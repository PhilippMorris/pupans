import os
from sys import argv

if __name__=='__main__':
    if len(argv) > 1:
        if argv[1] == "--poweroff":
            os.system('poweroff')
        elif argv[1] == "--reboot":
            os.system('reboot')
        else:
            print "Usage: 'python /opt/powercontrol.py --poweroff' or 'python /opt/powercontrol.py --reboot'"
    else:
        print "Usage: 'python /opt/powercontrol.py --poweroff' or 'python /opt/powercontrol.py --reboot'"



