#!/usr/bin/python
from argparse import ArgumentParser
import logging
import signal
import multiprocessing
import os
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning
from httpclient import HttpDownload
from torrentindex import TorrentIndex


log = logging.getLogger(__name__)
interrupt_event = multiprocessing.Event()


def interrupt():
    interrupt_event.set()


def run(seeder, torrents_folder, branch, ignore):
    log.info("Loading torrents index from seeder and comparing to local torrents folder...")
    index = TorrentIndex()
    index.load(seeder, branch, ignore)
    outdated_local_files = index.diff_local_folder(torrents_folder)

    session = requests.session()

    log.info('Found outdated_files=%s', len(outdated_local_files))

    for file in outdated_local_files:
        if interrupt_event.is_set():
            log.info('Interrupted...')
            break

        if file['name'] == 'storage.xml':
            # Do not override local symlinked storage XML
            continue

        with HttpDownload(session=session) as download:
            url = index.index[file['name']]['url']
            local_path = file['path']

            try:
                log.info('Download new torrent url=%s to path=%s', url, local_path)
                download.download_file(url, local_path)
            except IOError as e:
                log.error(e)

def getargs():
    parser = ArgumentParser()

    parser.add_argument('--torrents', type=str, default='torrents', help='Path to the folder containing the torrents.')
    parser.add_argument('--seeder', type=str, default='https://seeder.basechord.com', help='URL of the seeder.')
    parser.add_argument('--port', type=int, default=443, help='Port of the seeder.')
    parser.add_argument('--path', type=str, default='', help='Path on the seeder.')
    parser.add_argument('--branch', type=str, default='', help='Path to the branch on the seeder.')
    parser.add_argument('--seederuser', dest='seeder_user', type=str, default='p2p', help='User for authenticating to the seeder.')
    parser.add_argument('--seederpassword', dest='seeder_password', type=str, default='AppCh0rd', help='Password for authenticating to the seeder.')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--connecttimeout', dest='connect_timeout', default=10, help='HTTP connect timeout when connecting to the seeder.')
    parser.add_argument('--ignore', dest='ignore', type=str, default='', help='Torrent(s) that should be ignored. If any part of the torrent name matches the string specified, it will be skipped.')

    args = parser.parse_args()

    if not os.path.exists(args.torrents):
        raise IOError("Cannot find directory with torrents {0}.".format(args.torrents))

    if not re.match(r'^https?://.*$', args.seeder):
        raise ValueError("Parameter seeder is not a valid URL.")

    return args


def configure_logging(verbose):
    FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(message)s'
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format=FORMAT, level=level)

def stop(signum, frame):
    log.debug("Received signal " + str(signum))
    interrupt()

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
    requests.packages.urllib3.disable_warnings(SNIMissingWarning)
    args = getargs()

    configure_logging(args.verbose)

    # Configure components
    HttpDownload.user = args.seeder_user
    HttpDownload.password = args.seeder_password
    HttpDownload.connect_timeout = args.connect_timeout

    # Start downloading the jobs in the scheduler's queue.
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        run('{0}:{1}/{2}'.format(args.seeder, args.port, args.path), args.torrents, args.branch, args.ignore)
    except KeyboardInterrupt:
        # Simply exit
        pass