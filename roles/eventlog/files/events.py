#!/usr/bin/python

import argparse
import logging
import os
import lock
import configparser

from eventlog.gateway_rest import HttpRestGateway
from eventlog.gateway_servicebus import AzureServiceBusGateway
from eventlog.repository import MongoDbRepository
from eventlog.upload import EventUpload

__author__ = 'aluetjen'


def add(args):
    MongoDbRepository.host = args.mongodbhost
    MongoDbRepository.port = args.mongodbport

    repository = MongoDbRepository()
    repository.add(args.type, args.message)


def post(args):
    MongoDbRepository.host = args.mongodbhost
    MongoDbRepository.port = args.mongodbport

    HttpRestGateway.url = args.apiurl
    HttpRestGateway.user = args.apiuser
    HttpRestGateway.password = args.apipassword
    HttpRestGateway.ssl_insecure = args.apisslinsecure

    lock_file = '/var/run/events.pid' if os.name != 'nt' else 'events.pid'

    with lock.LockFile(lock_file):
        upload = EventUpload(simulation=args.whatif)
        upload.upload()


def post_azure(args):
    MongoDbRepository.host = args.mongodbhost
    MongoDbRepository.port = args.mongodbport

    AzureServiceBusGateway.namespace = args.sbnamespace
    AzureServiceBusGateway.issuer = args.sbissuer
    AzureServiceBusGateway.key = args.sbkey

    lock_file = '/var/run/events.pid' if os.name != 'nt' else 'events.pid'

    with lock.LockFile(lock_file):
        upload = EventUpload(simulation=True, gateway=AzureServiceBusGateway())
        upload.upload()

def discard(args):
    MongoDbRepository.host = args.mongodbhost
    MongoDbRepository.port = args.mongodbport

    repository = MongoDbRepository()
    repository.delete_all()


def list_events(args):
    MongoDbRepository.host = args.mongodbhost
    MongoDbRepository.port = args.mongodbport

    events = MongoDbRepository()

    for event in sorted(events.any()):
        print("{Date}\t{Type}\t{Details}".format(**event))


def parse_command_line():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'events.conf'))

    defaults_api = dict(config.items('Api')) if config.has_section('Api') else dict()
    defaults_sb = dict(config.items('ServiceBus')) if config.has_section('ServiceBus') else dict()
    defaults_mongo = dict(config.items('MongoDb')) if config.has_section('MongoDb') else dict()

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('type')
    add_parser.add_argument('message')
    add_parser.set_defaults(func=add)

    post_parser = subparsers.add_parser('post')
    post_parser.add_argument('--apiurl', type=str, default="http://localhost/api/session")
    post_parser.add_argument('--apiuser', type=str)
    post_parser.add_argument('--apipassword', type=str)
    post_parser.add_argument('--apisslinsecure', action='store_true')
    post_parser.add_argument('--whatif', action='store_true')

    post_parser.set_defaults(func=post)
    post_parser.set_defaults(**defaults_api)

    post_azure_parser = subparsers.add_parser('postazure')
    post_azure_parser.add_argument('--sbnamespace', type=str)
    post_azure_parser.add_argument('--sbkey', type=str)
    post_azure_parser.add_argument('--sbissuer', type=str)

    post_azure_parser.set_defaults(func=post_azure)
    post_azure_parser.set_defaults(**defaults_sb)

    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list_events)

    discard_parser = subparsers.add_parser('discard')
    discard_parser.set_defaults(func=discard)

    parser.add_argument('--mongodbhost', type=str, default="localhost")
    parser.add_argument('--mongodbport', type=int, default=27017)
    parser.set_defaults(**defaults_mongo)

    return parser.parse_args()


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    frmt = logging.Formatter('%(asctime)-15s %(levelname)s %(message)s')
    fh = logging.FileHandler('/var/log/eventrepository.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(frmt)
    logging.getLogger("EventRepository").addHandler(fh)


if __name__ == '__main__':
    configure_logging()

    args = parse_command_line()

    args.func(args)
