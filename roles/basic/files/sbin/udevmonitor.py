#!/usr/bin/python
import argparse
import logging
import os
import re
import sh
import threading
from datetime import datetime

LOGGER = logging.getLogger(__name__)


class Monitor:

    def __init__(self, added_event, device_filter):
        self.adapter_added = added_event
        self.device_filter = device_filter

    def monitor(self):
        LOGGER.info("Monitoring changes by {0}.".format(self.device_filter))

        sh.udevadm.monitor(_out=self._scan_for_events).wait()

    def _scan_for_events(self, line, stdin, process):

        match = re.search(self.device_filter, line)
        if match is not None:
            LOGGER.info("Detected: " + line)
            self.adapter_added.set()


def monitor(added_event, device_filter):
    adapter = Monitor(added_event, device_filter)
    adapter.monitor()


def restart(added_event, command):
    received_signal_on = None
    while True:
        if added_event.wait(5) and received_signal_on is None:
            added_event.clear()
            received_signal_on = datetime.utcnow()

        if received_signal_on is not None:
            if (datetime.utcnow() - received_signal_on).total_seconds() > 5:
                LOGGER.info('Running restart command...')

                received_signal_on = None
                os.system(command)


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


if __name__ == '__main__':
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument('--filter', dest='device_filter', default='.*', help=r'Example WLAN detection: UDEV.+add\s+/.+/net/wlan(.)\s\(net\)')
    parser.add_argument('command')
    args = parser.parse_args()

    device_added_event = threading.Event()

    restart_thread = threading.Thread(target=restart, args=(device_added_event, args.command))
    restart_thread.daemon = True
    restart_thread.start()

    monitor(device_added_event, args.device_filter)
