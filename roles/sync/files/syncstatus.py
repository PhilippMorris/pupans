#!/usr/bin/python

import sys
import argparse
import configparser
import os
import logging

from syncstatus.manager import Manager
from syncstatus.gateway import HttpRestGateway, AzureServiceBusGateway, EchoGateway

__author__ = 'lolsen'

LOGGER = logging.getLogger("syncstatus")


def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def post(args):
    # Configure components
    #
    HttpRestGateway.url = args.apiurl
    HttpRestGateway.user = args.apiuser
    HttpRestGateway.password = args.apipassword
    HttpRestGateway.ssl_insecure = args.apisslinsecure

    manager = Manager(getScriptPath(), args.downloads)

    if args.whatif :
        manager.gateway = EchoGateway()

    # Process
    #
    manager.process()

    LOGGER.info("Finished upload cycle.")


def post_azure(args):
    # Configure components
    #
    AzureServiceBusGateway.namespace = args.sbnamespace
    AzureServiceBusGateway.issuer = args.sbissuer
    AzureServiceBusGateway.key = args.sbkey

    manager = Manager(getScriptPath(), args.downloads)
    manager.gateway = AzureServiceBusGateway()

    # Process
    #
    manager.process()

    LOGGER.info("Finished upload cycle.")


def parse_command_line():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'syncstatus.conf'))

    defaults_api = dict(config.items('Api')) if config.has_section('Api') else dict()
    defaults_sb = dict(config.items('ServiceBus')) if config.has_section('ServiceBus') else dict()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    post_parser = subparsers.add_parser('post')
    post_parser.add_argument('--apiurl', type=str, default="http://localhost/api/syncstatus")
    post_parser.add_argument('--apiuser', type=str)
    post_parser.add_argument('--apipassword', type=str)
    post_parser.add_argument('--apisslinsecure', action='store_true')
    post_parser.add_argument('--whatif', action='store_true')
    post_parser.set_defaults(**defaults_api)
    post_parser.set_defaults(func=post)

    post_azure_parser = subparsers.add_parser('postazure')
    post_azure_parser.add_argument('--sbnamespace', type=str)
    post_azure_parser.add_argument('--sbkey', type=str)
    post_azure_parser.add_argument('--sbissuer', type=str)
    post_azure_parser.set_defaults(func=post_azure)
    post_azure_parser.set_defaults(**defaults_sb)

    parser.add_argument('--downloads', type=str, default='download', help='Path to the download folder.')

    return parser.parse_args()


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


if __name__ == "__main__":
    configure_logging()

    args = parse_command_line()

    args.func(args)
