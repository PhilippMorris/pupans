#!/usr/bin/python

import argparse
import logging
import requests
import json

__author__ = 'lolsen'

LOGGER = logging.getLogger("send_event")
POST_EVENT_URL = "http://localhost:80/event/"

def send(name, data):
    url = POST_EVENT_URL + name
    headers = {'content-type': 'application/json'}
    auth = None

    r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers, verify=False)

    if (not r.ok) or (200 > r.status_code > 299):
        raise IOError(("Failed to upload session to server. OK %s HTTP response code: %d" % (r.ok, r.status_code)))


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str)
    parser.add_argument('--jsondata', type=str, default='{}')

    return parser.parse_args()


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


if __name__ == "__main__":
    configure_logging()
    args = parse_command_line()
    data = json.loads(args.jsondata)
    send(args.name, data)
