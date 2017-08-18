#!/usr/bin/python

import socket
import argparse
import logging
from multiprocessing import Process
import datetime
from time import sleep
import sys


def ns_lookup(host, port):
    try:
        socket.getaddrinfo(host, port)
    except socket.gaierror:
        sys.exit(2)

if __name__ == '__main__':
    FORMAT = '%(created)d %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    LOGGER = logging.getLogger()

    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', default=15, type=int, help='Seconds to wait between tests.')
    parser.add_argument('--backoff', default=180, type=int, help='Seconds to back off in case of failure.')
    parser.add_argument('host', help='A host to resolve for test purposes.')
    parser.add_argument('port', help='The service port to resolve for.')
    args = parser.parse_args()

    backoff = False
    failed_on = None

    while True:

        start = datetime.datetime.utcnow()

        if backoff:
            if (datetime.datetime.utcnow() - failed_on).seconds >= args.backoff:
                failed_on = None
                backoff = False
            else:
                LOGGER.info('-')

        if not backoff:
            try:
                process = Process(target=ns_lookup, args=(args.host, args.port))
                process.daemon = True
                process.start()
                process.join(15)

                ms = int((datetime.datetime.utcnow() - start).microseconds/1000)

                if process.exitcode == 0:
                    logging.info("S={0}".format(ms))
                else:
                    logging.info('E={0}'.format(ms))

                try:
                    if process.is_alive():
                        process.terminate()
                except:
                    logging.error('Failed to kill child process.')
            except Exception as e:
                backoff = True
                logging.error('Failed to launch probe: ' + e.message)

        if backoff and failed_on is None:
            failed_on = datetime.datetime.utcnow()

        ms = int((datetime.datetime.utcnow() - start).microseconds/1000)
        delay = args.delay - (ms / 1000)

        sleep(delay)