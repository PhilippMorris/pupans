#!/usr/bin/python
from argparse import ArgumentParser
import logging
import signal
import os
import re
from downloader import Downloader
from httpclient import HttpDownload
from scheduler import Scheduler
from contentstorage import ContentStorage
from torrent import Torrent

log = logging.getLogger(__name__)


def interrupt():
    Downloader.interrupt()
    Scheduler.interrupt()


def getargs():
    parser = ArgumentParser()

    parser.add_argument('--torrents', type=str, default='torrents', help='Path to the folder containing the torrents.')
    parser.add_argument('--downloads', type=str, default='download', help='Path to the download folder.')
    parser.add_argument('--seeder', type=str, default='https://seeder.basechord.com', help='URL of the seeder.')
    parser.add_argument('--port', type=int, default=443, help='Port of the seeder.')
    parser.add_argument('--path', type=str, default='', help='Path on the seeder.')
#    parser.add_argument('--branch', type=str, default='', help='Path to the branch on the seeder.')
    parser.add_argument('--seederuser', dest='seeder_user', type=str, default='p2p', help='User for authenticating to the seeder.')
    parser.add_argument('--seederpassword', dest='seeder_password', type=str, default='AppCh0rd', help='Password for authenticating to the seeder.')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--downloaddelaymin', dest='download_delay_min', help='Minimum seconds to wait before starting a new download.')
    parser.add_argument('--downloaddelaymax', dest='download_delay_max', help='Maximum seconds to wait before starting a new download.')
    parser.add_argument('--errordelay', dest='error_delay', default=3, help='Seconds to wait after an error occurred. The delay increases each time another error occurrs by the backoff factor.')
    parser.add_argument('--errordelaybackoff', dest='error_delay_backoff', default=1.25, help='Factor by which to increase the delay after an error occurred.')
    parser.add_argument('--connecttimeout', dest='connect_timeout', default=10, help='HTTP connect timeout when connecting to the seeder.')
    parser.add_argument('--forcestoragelayout', dest='force_storage_layout', action='store_true', help='Force the use of astorage layout file (storage.xml).')
    parser.add_argument('--firstpriority', dest='first_priority', type=str, help='Torrent(s) that should be downloaded first. If any part of the torrent name matches the string specified, it will be downloaded first.')

    args = parser.parse_args()

    if not os.path.exists(args.downloads):
        os.makedirs(args.downloads)

    if not os.path.exists(args.torrents):
        raise IOError("Cannot find directory with torrents {0}.".format(args.torrents))

    if not re.match(r'^https?://.*$', args.seeder):
        raise ValueError("Parameter seeder is not a valid URL.")

    if args.download_delay_max is not None and args.download_delay_min is None or \
       args.download_delay_max is None and args.download_delay_min is not None:
        raise ValueError("You must specify both, min and max delay, or none at all.")

    args.download_delay_enabled = args.download_delay_max is not None and args.download_delay_min is not None

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
    args = getargs()

    configure_logging(args.verbose)

    # Configure components
    Scheduler.enable_job_delays = args.download_delay_enabled
    Scheduler.post_job_delay_max = args.download_delay_max
    Scheduler.post_job_delay_min = args.download_delay_min

#    Torrent.download_server = '{0}:{1}/{2}/{3}'.format(args.seeder, args.port, args.path, args.branch)
#    Torrent.local_download_path = args.downloads

    HttpDownload.user = args.seeder_user
    HttpDownload.password = args.seeder_password
    HttpDownload.connect_timeout = args.connect_timeout

    Downloader.delay_after_error = args.error_delay
    Downloader.delay_after_error_backoff_factor = args.error_delay_backoff

    # Scan for all available torrents and put them into the scheduler job queue.
    scheduler = Scheduler()
    scheduler.scan(args.torrents, args.first_priority)

    # Ensure that all folders from the storage layout have been
    # created and symlinked into the download folder. Not fully supported on Windows!
    layout_file = os.path.join(args.torrents, 'storage.xml')

    if os.path.exists(layout_file):
        log.info("Creating symlinks in %s", args.downloads)
        storage = ContentStorage()
        storage.load(layout_file)
        storage.ensure_all_content_folders_exist(args.downloads)
    elif args.force_storage_layout:
        raise IOError('Storage layout {layout_file} not found.'.format(**locals()))

    # Start downloading the jobs in the scheduler's queue.
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        scheduler.download()
    except KeyboardInterrupt:
        # Simply exit
        pass