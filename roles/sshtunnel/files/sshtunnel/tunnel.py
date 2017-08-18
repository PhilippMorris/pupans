#!/usr/bin/python
import logging
import threading
import argparse
import os
import sh
import subprocess
import re
import socket


class LogPipe(threading.Thread):
    def __init__(self, level):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.filter_expressions = []
        self.daemon = False
        self.level = level
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def filter(self, regex):
        self.filter_expressions.append(re.compile(regex))

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        for line in iter(self.pipeReader.readline, ''):
            skip = False
            for filter in self.filter_expressions:
                if filter.search(line) is not None:
                    skip = True
                    break

            if not skip:
                logging.log(self.level, line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)


def wait_for_internet_connection(host, port):
    logging.info('Waiting for Internet connection to {0} on port {1}...'.format(host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    while not connected:
        try:
            s.connect((host,int(port)))
            connected = True
            s.close()
        except Exception as e:
            logging.warning(e)
            time.sleep(1)
            pass #Do nothing, just try again


FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument('remote_host')
parser.add_argument('--remoteuser', dest='remote_user')
parser.add_argument('--remoteuserkey', dest='remote_user_sshkeyfile')
parser.add_argument('--remoteport', dest='remote_port', default=22)
parser.add_argument('--localport', dest='local_port', default=22)

args = parser.parse_args()

fqdn = sh.hostname('-f')

if not '.' in fqdn:
    raise ValueError("FQDN does not have a domain. Run 'hostname -f' to troubleshoot.")

if not os.path.exists(args.remote_user_sshkeyfile):
    raise IOError("SSH key file '{0}' for remote user does not exist.".format(args.remote_user_sshkeyfile))

wait_for_internet_connection(args.remote_host, args.remote_port)

logging.info('Allocating remote port...')

port = sh.ssh('-p', args.remote_port, '-o', 'UserKnownHostsFile=/dev/null',
              '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', '-o', 'BatchMode=yes',
              '-v', '-i', args.remote_user_sshkeyfile,
              '{0}@{1}'.format(args.remote_user, args.remote_host),
              '/opt/sshtunnel/port.py allocate {0}'.format(fqdn))

port = int(port.strip())

logging.info('Remote tunnel port {0} allocated.'.format(port))

logging.info('Launching autossh...')

infoPipe = LogPipe(logging.INFO)
debugPipe = LogPipe(logging.DEBUG)

debugPipe.filter(r'keepalive@openssh.com')

try:
    subprocess.call(('autossh', '-t', '-M', '0', '-nNT', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no',
                      '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-o', 'ExitOnForwardFailure=yes',
                      '-R', '{0}:localhost:{1}'.format(port, args.local_port), '-p', args.remote_port,
                      '-v', '-i', args.remote_user_sshkeyfile, '{0}@{1}'.format(args.remote_user, args.remote_host)),
                      stderr=debugPipe, stdout=infoPipe)
finally:
    infoPipe.close()
    debugPipe.close()