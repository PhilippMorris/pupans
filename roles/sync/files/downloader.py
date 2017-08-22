import logging
import threading
import os
import hashlib
import datetime
import io
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning
from requests.packages.urllib3.exceptions import ReadTimeoutError
from httpclient import HttpDownload, ContentUnavailableError

__author__ = 'aluetjen'

log = logging.getLogger(__name__)


class Stats:
    def __init__(self):
        self.bytes_downloaded_total = 0
        self.bytes_downloaded_rate = 0
        self.bytes_confirmed = 0
        self.start_time = None
        self.download_time = 0

        self.pieces_completed = 0
        self.pieces_downloaded = 0


class Downloader:
    delay_after_error = 3
    delay_after_error_backoff_factor = 1.75
    max_retries = 10
    log_rate_in_bytes = 1024 * 1024 * 100
    _state_file_mgrace = 60
    _ascii_zero = 48
    _ascii_one = 49

    _stop_event = threading.Event()

    @staticmethod
    def interrupt():
        Downloader._stop_event.set()

    def __init__(self, torrent, state_file):
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
        requests.packages.urllib3.disable_warnings(SNIMissingWarning)
        self.torrent = torrent
        self.state_file = state_file
        self.pieces_completed = bytearray()
        self.number_of_pieces = self.torrent.get_number_of_pieces()
        self.complete_file_path = os.path.join(self.torrent.local_root_path, '.complete')
        self.session = requests.session()
        self.delay_after_error = Downloader.delay_after_error
        self.max_retries = Downloader.max_retries

        self.stats = Stats()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.session is not None:
            self.session.close()

    def _is_piece_complete(self, index):
        return self.pieces_completed[index] == Downloader._ascii_one

    def _set_piece_complete(self, index, save=True):
        self.pieces_completed[index] = Downloader._ascii_one
        if save:
            self._save_state()

    def _save_state(self):
        with open(self.state_file, 'wb') as file:
            file.write(self.pieces_completed)

    def _load_state(self):
        has_state_file = False
        if os.path.exists(self.state_file):
            with open(self.state_file, 'rb') as file:
                completed_flags = file.read()
                self.pieces_completed = bytearray(completed_flags)

            if len(self.pieces_completed) == self.number_of_pieces:
                has_state_file = True
            else:
                log.warn("Corrupt state file=%s. Will rehash data.", self.state_file)

        if has_state_file:
            state_mtime = os.path.getmtime(self.state_file)

            for local_file, local_length in self.torrent.get_local_files():
                if not os.path.exists(local_file):
                    continue

                # Check if file has been modified
                time_delta = os.path.getmtime(local_file) - state_mtime
                if time_delta > Downloader._state_file_mgrace:
                    log.info("Ignoring state file=%s since downloaded content=%s has been modified %s seconds after.",
                             self.state_file, local_file, time_delta)
                    has_state_file = False
                    break

                # Check if file is too long
                if os.path.getsize(local_file) > local_length:
                    log.info("Truncating too long content file=%s to length=%s",
                             local_file, local_length)
                    with open(local_file, 'rb+') as file:
                        file.truncate(local_length)

        if not has_state_file:
            log.info("Rehashing existing data for torrent=%s", self.torrent.name)

            self.pieces_completed = bytearray(self.number_of_pieces)
            for i in range(0, len(self.pieces_completed)):
                self.pieces_completed[i] = Downloader._ascii_zero

            self._rehash()

    def _rehash(self):
        for piece_index in range(0, self.number_of_pieces):
            self._rehash_piece(piece_index)

        self._save_state()

    def _rehash_piece(self, index):
        request = self.torrent.get_piece_request(index)
        piece_bytes = bytearray(request.length)
        piece_bytes_view = memoryview(piece_bytes)
        offset = 0

        for file in request.files:
            if Downloader._stop_event.is_set():
                raise KeyboardInterrupt()

            if not os.path.exists(file.local_path):
                # Missing files means piece is obviously not complete yet
                return

            if os.path.getsize(file.local_path) < file.local_offset:
                # Missing data
                return

            with io.open(file.local_path, 'rb') as local_file:
                local_file.seek(file.local_offset, 0)
                while True:
                    try:
                        bytes_read = local_file.readinto(piece_bytes_view[offset:offset + file.piece_length])
                        offset += bytes_read
                        if bytes_read != file.piece_length:
                            # Didn't get enough data: incomplete piece
                            return
                    except IOError as e:
                        os.remove(file.local_path)
                        continue
                    break

        # Calculate checksum of piece data
        sha1 = hashlib.sha1(piece_bytes)

        if sha1.digest() == request.checksum:
            log.debug("Data matches hash, pieceIndex=%s, torrent=%s", index, self.torrent.name)
            self._set_piece_complete(index, save=False)
        else:
            log.debug("Mismatched hash, pieceIndex=%s, torrent=%s", index, self.torrent.name)

    def _download_piece(self, piece_index):
        request = self.torrent.get_piece_request(piece_index)
        piece_bytes = []
        start_transfer = datetime.datetime.now()
        for file in request.files:
            with HttpDownload(self.session) as client:
                if not os.path.exists(os.path.dirname(file.local_path)):
                    # Do not use exist_ok: it does not deal with symlinks as we expect
                    os.makedirs(os.path.dirname(file.local_path))

                if not os.path.exists(file.local_path):
                    mode = 'wb'
                else:
                    mode = 'rb+'

                with open(file.local_path, mode) as local_file:
                    stream = client.download_range(file.remote_url, file.remote_offset, file.piece_length)

                    local_file.seek(file.local_offset, 0)

                    while True:
                        if Downloader._stop_event.is_set():
                            raise KeyboardInterrupt()

                        buffer = stream.read(1024)
                        if len(buffer) == 0:
                            break
                        local_file.write(buffer)
                        piece_bytes.extend(buffer)

                        self.stats.bytes_downloaded_rate += len(buffer)
                        self.stats.bytes_downloaded_total += len(buffer)

        # Update stats
        time_taken_seconds = (datetime.datetime.now() - start_transfer).total_seconds()
        self.stats.download_time += time_taken_seconds

        # Verify piece
        if len(piece_bytes) < request.length:
            raise IOError("Short read. More response bytes expected.")

        # Calculate checksum of piece data
        sha1 = hashlib.sha1(bytearray(piece_bytes))
        sha_digest = sha1.digest()

        log.debug("Piece hash=%s", sha1.hexdigest())

        if sha_digest != request.checksum:
            raise IOError("Checksum failed.")

        self.stats.bytes_confirmed += len(piece_bytes)

    def _create_complete_file(self):
        if not os.path.exists(self.complete_file_path):
            with open(self.complete_file_path, 'wb'):
                # Simply create an empty file
                pass

    def _remove_complete_file(self):
        if os.path.exists(self.complete_file_path):
            os.remove(self.complete_file_path)

    def _make_read_only(self):
        for root, dirs, files in os.walk(self.torrent.local_root_path):
            for directory in dirs:
                os.chmod(os.path.join(root, directory), 0o555)
            for file in files:
                os.chmod(os.path.join(root, file), 0o444)

    def download(self):

        self.stats.start_time = datetime.datetime.now()

        self._load_state()

        first_piece = True

        for piece_index in range(0, self.number_of_pieces):
            retry_counter = 0

            if self._is_piece_complete(piece_index):
                log.debug("Piece already complete, pieceIndex=%s, torrent=%s",
                          piece_index, self.torrent.name)
                self.stats.pieces_completed += 1
                continue

            if first_piece and piece_index > 0:
                log.info("Resuming torrent=%s at pieceIndex=%s.", self.torrent.name, piece_index)

            first_piece = False
            current_delay = self.delay_after_error

            while True:
                retry = False
                try:
                    self._download_piece(piece_index)
                    self._set_piece_complete(piece_index)

                    self.stats.pieces_completed += 1
                    self.stats.pieces_downloaded += 1
                except (IOError, ContentUnavailableError, ReadTimeoutError) as e:
                    log.error("Failed to download piece torrent=%s, piece=%s, retryCount=%s",
                              self.torrent.name, piece_index, retry_counter)
                    log.exception(e)

                    # Recreate session to reestablish connection, potentially to a more
                    # healthy server or simply on a healthy connection. This also allows
                    # other clients to establish a connection in case this particular client
                    # is causing the error and hugging the connection on the server.
                    log.debug('Closing connection pool and delaying by %s seconds.', current_delay)

                    self.session.close()

                    if Downloader._stop_event.wait(current_delay):
                        raise KeyboardInterrupt()

                    current_delay *= Downloader.delay_after_error_backoff_factor

                    # Recreate session after delay
                    self.session = requests.session()

                    retry = True
                    retry_counter += 1

                    if retry_counter > self.max_retries:
                        raise

                if not retry:
                    break

            self._log_progress()

        self._log_progress(force=True)

        self._create_complete_file()
        self._make_read_only()

    def _log_progress(self, force=False):
        time_taken_seconds = (datetime.datetime.now() - self.stats.start_time).total_seconds()
        bytes_per_second_effective = 0
        if time_taken_seconds > 0:
            bytes_per_second_effective = int(self.stats.bytes_confirmed / time_taken_seconds)

        bytes_per_second = 0
        if self.stats.download_time > 0:
            bytes_per_second = int(self.stats.bytes_downloaded_rate / self.stats.download_time)

        aggregated_log_entry_due = self.stats.bytes_downloaded_rate >= Downloader.log_rate_in_bytes

        if aggregated_log_entry_due or force:
            log.info(
                "Progress torrent=%s, progress=%s%%, piecesFinished=%s, piecesDownloaded=%s, piecesTotal=%s, bytesDownloaded=%s, bytesConfirmed=%s, bytesPerSecond=%s, bytesPerSecondEffective=%s",
                self.torrent.name, 100 * self.stats.pieces_completed / self.number_of_pieces, self.stats.pieces_completed, self.stats.pieces_downloaded,
                self.number_of_pieces, self.stats.bytes_downloaded_total, self.stats.bytes_confirmed, bytes_per_second, bytes_per_second_effective)

            # Reset stats
            self.stats.bytes_downloaded_rate = 0
            self.stats.download_time = 0