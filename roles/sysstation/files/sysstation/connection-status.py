from netdevice import NetConnection
from netdevice import NetConnection
from time import sleep
import os
import subprocess
import socket
from sys import argv
import json
import argparse

def test_connection(server, port, protocol, retries):
    while retries > 0:
        retries = retries - 1
        try:
            s = socket.socket(socket.AF_INET, protocol)
            s.settimeout(1)
            s.connect((server, port))
            s.close()
            s = None
            return True
        except socket.error:
            s.close()
            s = None
            continue
    return False

def is_online(retries):
    if get_carrier():
        return test_connection("8.8.8.8", 53, socket.SOCK_DGRAM, retries) and \
            test_connection("api.ar.appchord.com", 443, socket.SOCK_STREAM, retries)
    else:
        return False

def get_carrier():
    carrier = open("/sys/class/net/eth0/carrier").read().rstrip('\n')
    return carrier == "1"

def send_event(online, connection, last_online, last_connection, link, last_link):
    if not (online == last_online) or not (connection == last_connection) or not (link == last_link):
        connection_changed = True

        if not link:
            send_online = "false"
            send_Name = "null"
            send_Description = "null"
            send_Port = "null"
        else:
            send_online = json.dumps(online)
            send_Name = json.dumps(connection.Name)
            send_Description = json.dumps(connection.Description)
            send_Port = json.dumps(connection.Port)

        try:
            st = "/opt/kiosk/send_event.py --name connection-status --jsondata \'{\"isOnline\":%s,\"name\":%s,\"description\":%s,\"port\":%s}\'" % (
                send_online, send_Name, send_Description, send_Port)
            print st
            os.system(st)
            if online and last_online == False:
                subprocess.Popen("/opt/eventlog/eventlog_post.sh")
        except:
            pass
        return connection_changed, online, connection, link
    else:
        connection_changed = False
        return connection_changed, None, None, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--persist', action='store_true', help="Persistently monitor connection status, do not close.")
    parser.add_argument('--interval', type=int, default=20, help='Number of seconds to delay between polling connection status.')
    parser.add_argument('--resend', type=int, default=30, help='Number of minutes to delay between resending offline status.')
    parser.add_argument('--retries', type=int, default=10, help='Number of retries to connect.')

    args = parser.parse_args()

    # Create connection object for start (empty values)
    link = None
    last_link = None
    connection = None
    last_connection = None
    online = None
    last_online = None
    time_offline = 0
    max_time_offline = args.resend * 60

    while True:
        connection = NetConnection(False)
        link = get_carrier()
        online = is_online(args.retries)
        if not online:
            time_offline += args.interval
            if time_offline >= max_time_offline:
                send_event(online, connection, None, None, link, None)
                time_offline = 0
        else:
            time_offline = 0
        new_values = send_event(online, connection, last_online, last_connection, link, last_link)
        if new_values[0]:
            last_online = new_values[1]
            last_connection = new_values[2]
            last_link = new_values[3]

        if args.persist:
            sleep(args.interval)
        else:
            break