import logging
import os
import re
import time
import urlparse
from httpclient import HttpDownload

log = logging.getLogger(__name__)


class TorrentIndex:
    def __init__(self):
        self.index = dict()

    def load(self, server, branch, ignore):
        with HttpDownload() as download:
            index_page = download.download_text('{0}/torrents/{1}/'.format(server, branch))

        href_regex = re.compile(r'<a\shref="(.+)">(.+)</a>\s+(\d+-\w{3}-\d+\s\d+:\d+)\s+(\d+)')

        for line in index_page.splitlines():
            match = href_regex.match(line)
            if match is not None:
                fileName = urlparse.unquote(match.group(1))
                if ignore != '' and ignore in fileName:
                    log.info('Skipping %s. File name matches the ignore string %s.', match.group(2), ignore)
                    continue

                remote_mtime = time.strptime(match.group(3), '%d-%b-%Y %H:%M')
                remote_size = int(match.group(4))

                self.index[fileName] = dict(
                    url='{0}/torrents/{1}/{2}'.format(server, branch, match.group(1)), name=fileName,
                    timestamp=remote_mtime, size=remote_size)

        log.debug('Found %s references on index page.', len(self.index))

    def diff_local_folder(self, local_folder):
        outdated_local_files = []

        for name, entry in self.index.items():
            reason = None
            local_file_path = os.path.join(local_folder, name)

            if not os.path.exists(local_file_path):
                reason='Not found'
            else:
                local_file_mtime = time.gmtime(os.path.getmtime(local_file_path))
                local_file_size = os.path.getsize(local_file_path)

                if local_file_mtime < entry['timestamp']:
                    reason = 'Modified'

                if local_file_size != entry['size']:
                    reason = 'File size mismatch.'

            if reason is not None:
                outdated_local_files.append(dict(name=name, path=local_file_path, reason=reason))

        return outdated_local_files