#!/usr/bin/python
import argparse
import logging
import re
from time import sleep
import yaml
import os
import subprocess

if os.name != 'nt':
    import fcntl
    import sh
else:
    import pbs as sh

__author__ = 'aluetjen'


class PortAllocationTable:
    def __empty_pat(self):
        return {'hosts': {}}

    def __init__(self, path, read_only=True):
        self.path = path

        if read_only:
            self.__file = None
            if os.path.exists(path):
                with open(path, 'r') as pat_file:
                    self.pat = yaml.load(pat_file)
            else:
                self.pat = None
        else:
            mode = 'r+' if os.path.exists(self.path) else 'w+'

            self.__file = open(self.path, mode)

            if os.name != 'nt':
                fcntl.lockf(self.__file, fcntl.LOCK_EX | fcntl.LOCK_NB)

            self.pat = yaml.load(self.__file)

        if self.pat is None:
            self.pat = self.__empty_pat()

    def save(self):
        self.__file.truncate(0)
        self.__file.seek(0)
        yaml.safe_dump(self.pat, self.__file, default_flow_style=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__file is not None:
            self.__file.close()

    def hosts(self):
        return self.pat['hosts']


class PortRepository:
    def __init__(self, pat_file, min_port=22100, max_port=31999):
        self.pat_file = pat_file
        self.min_port = min_port
        self.max_port = max_port

    def lookup_port(self, host):
        with PortAllocationTable(self.pat_file) as pat:
            if host in pat.hosts():
                return pat.hosts()[host]

    def allocate(self, host):

        port = self.lookup_port(host)

        if port is None:
            last_port = self.min_port - 1

            with PortAllocationTable(self.pat_file, read_only=False) as pat:
                if host in pat.hosts():
                    port = pat.hosts()[host]
                else:
                    for port in sorted(pat.hosts().values()):
                        if last_port is None or port - last_port > 0:
                            last_port = port
                        else:
                            break

                    port = last_port+1
                    pat.hosts()[host] = port

                if port > self.max_port:
                    raise ValueError("Max port {0} exceeded".format(self.max_port))

                pat.save()

        return port


class Monitor:
    def __init__(self):
        self.pat = None
        self.listening_ports = {}
        self.last_status = {}

    def load_status(self, status_path):
        with open(status_path, "r") as status_file:
            self.last_status = yaml.load(status_file)

    def save_status(self, status_path):
        temp_file = os.tempnam()

        with open(temp_file, "w") as status_file:
            yaml.safe_dump(self.last_status, status_file)

        if os.path.exists(status_path):
            os.remove(status_path)
        os.rename(temp_file, status_path)

    def load_pat(self, pat_file):
        self.pat = PortAllocationTable(pat_file, read_only=True)

    def scan_ports(self):
        self.listening_ports = {}
        listening_ports_raw = sh.netstat('-ln')

        for listener in listening_ports_raw:
            match = re.match("tcp\\s+\\d+\\s+\\d+\\s+127\\.0\\.0\\.1:(\\d+)\\s+0\\.0\\.0\\.0:\\*\\s*LISTEN", listener)
            if match is not None:
                self.listening_ports[int(match.group(1))] = 1

        return self.listening_ports

    def status(self):
        self.last_status = {}
        for host, port in self.pat.hosts().iteritems():
            if self.listening_ports.has_key(port):
                self.last_status[host] = "online"
            else:
                self.last_status[host] = "offline"

        return self.last_status

    def monitor(self, pat_file):
        previous_status = self.last_status.copy()

        self.load_pat(pat_file)
        self.scan_ports()

        new_status = self.status()

        updates = {}

        for host, status in previous_status.iteritems():
            updates[host] = (status, None)

        for host, status in new_status.iteritems():
            tuple = updates.get(host)
            if tuple is None:
                updates[host] = (None,status)
            else:
                updates[host] = (updates[host][0], status)

        events = []

        for host, update in updates.iteritems():
            event = 'stable'
            if update[0] != update[1]:
                if update[1] == "offline":
                    event = 'disconnected'
                elif update[1] == "online":
                    event = 'connected'
            events.append({'host': host, 'status': update[1], 'event': event})

        return events

def allocate(args):
    port_repository = PortRepository(args.pat)
    print(port_repository.allocate(args.host))


def find(args):
    port_repository = PortRepository(args.pat)
    print(port_repository.lookup_port(args.host))


def connect(args):
    port_repository = PortRepository(args.pat)
    port = port_repository.lookup_port(args.host)

    if port is None:
        raise LookupError("Cannot find reverse tunnel port.")

    subprocess.call(('ssh', '{0}@localhost'.format(args.user), '-p', str(port)))


def monitor(args):
    monitor = Monitor()

    while True:
        for event in monitor.monitor(args.pat):
            print event

        sleep(args.interval)


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser()

    sub_parser = parser.add_subparsers()

    upsert_parser = sub_parser.add_parser('allocate')
    upsert_parser.set_defaults(func=allocate)

    connect_parser = sub_parser.add_parser('connect')
    connect_parser.add_argument('--user', default='acadmin')
    connect_parser.set_defaults(func=connect)

    monitor_parser = sub_parser.add_parser('monitor')
    monitor_parser.add_argument('--interval', type=int, default=60, help="Runs the connection check ever interval.")
    monitor_parser.set_defaults(func=monitor)

    parser.add_argument('host', help='The FQDN of the host.')
    parser.add_argument('--pat', help='The port allocation table to use.', default='/opt/sshtunnel/pat')

    args = parser.parse_args()
    args.func(args)