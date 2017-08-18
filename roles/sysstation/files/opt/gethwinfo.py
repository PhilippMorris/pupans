import os
import subprocess

def get_servicetag():
    p = subprocess.Popen(["dmidecode", "-s", "system-serial-number"], stdout=subprocess.PIPE)
    return p.stdout.read().rstrip('\n')




if __name__=='__main__':
    try:
        str = '/opt/eventlog/events.py add \'StationInfo\' "{ServiceTag: \'%s\'}"' % get_servicetag()
        os.system(str)
    except Exception as e:
        print e





