#!/usr/bin/python
import os
import geoip2.webservice
import requests
import json
import argparse
import logging
import pytz
import datetime

LOGGER = logging.getLogger(__name__)


def locate():
    response = requests.get('http://ifconfig.me/ip', headers={})

    if response.status_code != 200:
        raise IOError('Failed to lookup public ip.')

    ip = response.content.strip()

    LOGGER.debug('ip=%s', ip)

    client = geoip2.webservice.Client(78506, 'Bu5OUYHbNUuY')
    geoip_lookup_data = client.city(ip)

    with open('geolocate.cache', 'w') as cache:
        json.dump(geoip_lookup_data.raw, cache)

    return geoip_lookup_data.raw


def utcoffset():
    geoip_lookup_data = None

    if os.path.exists('geolocate.cache'):
        with open('geolocate.cache', 'r') as cache:
            geoip_lookup_data = json.load(cache)

    if geoip_lookup_data is None:
        geoip_lookup_data = locate()

    timezone = pytz.timezone(geoip_lookup_data['location']['time_zone'])
    utc_offset_hours = timezone.utcoffset(datetime.datetime(2000, 1, 1)).total_seconds()/60/60

    LOGGER.debug('utcOffset=%s', utc_offset_hours)

    return int(utc_offset_hours)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    utcoffset_parser = subparser.add_parser('utcoffset')
    utcoffset_parser.set_defaults(action=utcoffset)

    locate_parser = subparser.add_parser('locate')
    locate_parser.set_defaults(action=locate)

    args = parser.parse_args()

    print args.action()