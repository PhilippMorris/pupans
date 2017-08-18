import logging
import os
import re

__author__ = 'aluetjen'

import requests

log = logging.getLogger(__name__)


class ContentUnavailableError(Exception):
    pass


class HttpDownload:
    user = None
    password = None
    session = requests.session()
    connect_timeout = 10

    def __init__(self, session=None):
        self.session = session if session is not None else HttpDownload.session
        self.content_range = None
        self.response = None
        self.user = HttpDownload.user
        self.password = HttpDownload.password
        self.connect_timeout = HttpDownload.connect_timeout

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.response is not None:
            self.response.close()

    def download_file(self, url, local_file):

        response = self._download(url)

        tmp_filename = local_file + '.tmp'
        with open(tmp_filename, 'wb') as file:
            file.write(response.content)

        if os.path.exists(local_file):
            os.remove(local_file)

        os.rename(tmp_filename, local_file)

    def download_text(self, url):
        return self._download(url).text

    def _download(self, url):
        """
        :rtype: str
        """

        if self.user is not None:
            auth = (self.user, self.password)
        else:
            auth = None

        self.response = self.session.get(url, auth=auth, stream=False, verify=False, timeout=self.connect_timeout)

        status_code = self.response.status_code

        if status_code < 200 or status_code >= 400:
            log.debug("Failed to download resource, url=%s, statusCode=%s", url, status_code)
            raise IOError("Failed to download statusCode=" + str(status_code))

        return self.response

    def download_range(self, url, offset, length):
        """
        :rtype: urllib3.HTTPResponse
        """

        end = offset + length - 1

        headers = {
            'Range': 'bytes={offset}-{end}'.format(**locals()),
            'Accept-Encoding': 'identity'
        }

        if self.user is not None:
            auth = (self.user, self.password)
        else:
            auth = None

        self.response = self.session.get(url, auth=auth, stream=True, verify=False, headers=headers,
                                         timeout=self.connect_timeout)

        status_code = self.response.status_code

        if status_code == 404:
            raise ContentUnavailableError()

        if not 200 <= status_code < 300:
            log.debug("Failed to download range, url=%s, statusCode=%s", url, status_code)
            raise IOError("Failed to download statusCode=" + str(status_code))

        # Decode returned range
        if status_code != 206 or 'content-range' not in self.response.headers:
            raise IOError("Failed to retrieve range.")

        content_range = self.response.headers['Content-Range']

        match = re.match('bytes (\d+)-(\d+)/(\d+)', content_range)
        self.content_range = dict(
            offsetStart=int(match.group(1)),
            offsetEnd=int(match.group(2)),
            total=int(match.group(3)))

        if not self.content_range['offsetStart'] == offset:
            raise IOError("Server return content from different offset.")

        log.debug("Response for url=%s, offsetStart=%s, offsetEnd=%s",
                  url, self.content_range['offsetStart'], self.content_range['offsetEnd'])

        return self.response.raw