#!/usr/bin/python
import logging
import xml.etree.ElementTree as ET
import os
import shutil
import argparse

log = logging.getLogger(__name__)


class NoSpecError(Exception):
    def __init__(self, folder):
        self.folder = folder

    def __str__(self):
        return 'There is no specification where to store {0}.'.format(self.folder)


class ContentStorage:
    def __init__(self):
        self.layout = None

    def load(self, layout_file=None, layout=None):

        if layout_file is not None:
            self.layout_file = ET.parse(layout_file)
            self.layout = self.layout_file.getroot()
        elif layout is not None:
            self.layout = ET.fromstring(layout)
        else:
            raise ValueError('Need to pass file or layout.')

    def add_content_folder(self, new_folder):
        spec = self.layout.find("*/folder[@name='{0}']".format(new_folder))

        if spec is not None:
            raise ValueError('There is a folder {0} already'.format(new_folder))

        drive_usage = {}

        for drive in self.layout.findall('drive'):
            drive_usage_temp = 0
            for folder in drive.findall('folder'):
                drive_usage_temp += 1
            drive_usage[drive] = drive_usage_temp

        drive = min(drive_usage, key=drive_usage.get)

        if drive is None:
            raise ValueError('No drive defined in storage layout.')

        ET.SubElement(drive, 'folder', {'name': new_folder})

    def add_drive(self, new_drive):
        if not os.path.exists(new_drive):
            raise IOError('Cannot find drive {0} on local file system.'.format(new_drive))

        spec = self.layout.find("drive[@path='{0}']".format(new_drive))

        if spec is not None:
            raise ValueError('There is a drive {0} already.'.format(new_drive))

        ET.SubElement(self.layout, 'drive', {'path': new_drive})

    def ensure_content_folder_exists(self, folder, download_dir):
        spec = self.layout.find("*/folder[@name='{0}']".format(folder))

        if spec is None:
            raise NoSpecError(folder)

        drive = self.layout.find("*/folder[@name='{0}']/..".format(folder))

        content_path = os.path.join(drive.get('path'), spec.get('name'))

        if os.name == 'nt':
            content_path = content_path.replace("/", "\\")

        if not os.path.exists(content_path):
            os.makedirs(content_path)

        content_path_download = os.path.join(download_dir, spec.get('name'))

        if os.path.lexists(content_path_download) and os.path.islink(content_path_download):
            current_link = os.readlink(content_path_download)

            if current_link != content_path:
                log.info('Fixing symlink target %s -> %s', current_link, content_path)
                os.remove(content_path_download)
                log.info('Creating symlink %s -> %s', content_path, content_path_download)
                os.symlink(content_path, content_path_download)
        else:
            if os.name != 'nt':
                if os.path.exists(content_path_download):
                    log.info('Remove bad path %s to replace with symlink.', content_path_download)
                    if os.path.isdir(content_path_download):
                        shutil.rmtree(content_path_download)
                    else:
                        os.remove(content_path_download)

                log.info('Creating symlink %s -> %s', content_path, content_path_download)
                os.symlink(content_path, content_path_download)

        return content_path_download, content_path

    def ensure_all_content_folders_exist(self, download_dir):
        for folder in self.layout.iter('folder'):
            log.debug("Checking symlinks for folder %s", folder.get('name'))
            self.ensure_content_folder_exists(folder.get('name'), download_dir)

    def save(self, layout_file):
        self.layout_file.write(layout_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('action', type=str)
    parser.add_argument('--spec', type=str, default='/usr/share/p2pclient/torrents/storage.xml')
    parser.add_argument('--downloaddir', type=str, default='/usr/share/p2pclient/download')
    parser.add_argument('folder', type=str)

    args = parser.parse_args()

    storage = ContentStorage()
    storage.load(args.spec)

    if args.action == 'ensure':
        storage.ensure_content_folder_exists(args.folder, args.downloaddir)
    elif args.action == 'ensureall':
        storage.ensure_all_content_folders_exist(args.downloaddir)
    elif args.action == 'add':
        storage.add_content_folder(args.folder)
        storage.save(args.spec)
    elif args.action == 'adddrive':
        storage.add_drive(args.folder)
        storage.save(args.spec)
