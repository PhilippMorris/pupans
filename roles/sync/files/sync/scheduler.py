import logging
import os
import threading
from random import randint
import re
from downloader import Downloader
from httpclient import ContentUnavailableError
from torrent import Torrent

__author__ = 'aluetjen'

log = logging.getLogger(__name__)


def job_sort_order(job):
    return -job.download_first, -job.priority, job.torrent_created


class Scheduler:
    enable_job_delays = False
    post_job_delay_min = 60
    post_job_delay_max = 60 * 60

    _stop_event = threading.Event()

    @staticmethod
    def interrupt():
        Scheduler._stop_event.set()

    def __init__(self):
        self.jobs = []
        self.firstPrioritySku = None

    def scan(self, torrent_directory, first_priority):
        file_name_re = re.compile(r'^.*#\d+\.torrent$')

        for file in os.listdir(torrent_directory):
            if file_name_re.match(file) is None:
                log.debug('Skipping %s. File name does not match expression %s.', file, file_name_re.pattern)
                continue

            job = Job(os.path.join(torrent_directory, file))
            if first_priority is not None:
                job.download_first = first_priority in file
            self.jobs.append(job)

            log.info('Added torrent=%s\tpriority=%s\tcreated date=%s', job.torrent_file, job.priority,
                     job.torrent_created)

        self.jobs.sort(key=job_sort_order)

    def download(self):
        for job_index in range(0, len(self.jobs)):
            job = self.jobs[job_index]

            if job.is_pending():
                log.info("Start torrent=%s", job.torrent_file)

                try:
                    job.download()
                except ContentUnavailableError:
                    log.error("Skipping torrent=%s. Its content is unavailable.", job.torrent_file)
                    continue

                if Scheduler.enable_job_delays:
                    delay = randint(Scheduler.post_job_delay_min, Scheduler.post_job_delay_max)

                    log.info('Delay next torrent for %s seconds.', delay)
                    if Scheduler._stop_event.wait(timeout=delay):
                        raise InterruptedError()
            else:
                log.info("Done torrent=%s", job.torrent_file)

        log.info("Done all torrents=%s", len(self.jobs))


class Job:
    def __init__(self, torrent_file):
        self.torrent_file = torrent_file
        self.state_file = torrent_file + ".state"
        torrent = Torrent()
        torrent.load(self.torrent_file)
        self.torrent_created = torrent.creation_date
        self.priority = torrent.priority

    def is_pending(self):
        if not os.path.exists(self.state_file):
            return True

        with open(self.state_file, 'r') as file:
            first_line = file.read(len('complete'))

            if first_line == "complete":
                return False

        return True

    def download(self):
        torrent = Torrent()
        torrent.load(self.torrent_file)

        with Downloader(torrent, self.state_file) as downloader:
            downloader.download()

        with open(self.state_file, "w") as file:
            file.write('complete')
