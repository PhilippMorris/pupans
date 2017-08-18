#!/usr/bin/python

import argparse
import logging
import os
import shutil
import glob
import json
from subprocess import call

__author__ = 'lolsen'

LOGGER = logging.getLogger('apply_media')
POST_EVENT_URL = 'http://localhost:80/event/'
EXCLUDE_FILE_NAME = 'apply_media_exclude.txt'
MEDIA_PACKAGES_PATH = '/srv/media/'

def unmount_device(device):
    partitions = glob.glob('/dev/' + device + '?')
    call(['umount'] + partitions)

def mount_device(device):
    partition = device + '1'
    device_path = '/dev/' + partition
    mount_path = '/mnt/' + partition

    if os.path.exists(mount_path):
        shutil.rmtree(mount_path)
    os.makedirs(mount_path)
    call(['mount', device_path, mount_path])  # mount /dev/sdc1 /mnt/sdc1
    return mount_path

def format_media(device, file_system):
    unmount_device(device)
    call(['parted', '--script', '/dev/' + device, 'mklabel', 'msdos'])  # parted --script /dev/sdc mklabel msdos
    file_system = file_system.lower()
    if file_system == 'fat32':
        call(['parted', '--script', '/dev/' + device, 'mkpart', 'primary', 'fat32', '0%', '100%']) #parted --script /dev/sdc mkpart primary fat32 0% 100%
        unmount_device(device)
        call(['mkfs.vfat', '-F32', '/dev/' + device + '1'])  # mkfs.vfat /dev/sdc1
    elif file_system == 'ntfs':
        call(['parted', '--script', '/dev/' + device, 'mkpart', 'primary', 'ntfs', '0%', '100%']) #parted --script /dev/sdc mkpart primary ntfs 0% 100%
        unmount_device(device)
        call(['mkfs.ntfs', '--fast', '/dev/' + device + '1'])  # mkfs.ntfs /dev/sdc1
    else:
        raise ValueError('{file_system} is not a valid file system. Use "fat32" or "ntfs".'.format(file_system=repr(file_system)))

def copy_directory(directory, device):
    mount_path = mount_device(device)
    exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCLUDE_FILE_NAME)
    call(['rsync', '--recursive', '--copy-links', '--exclude-from', exclude_file, directory + '/', mount_path + '/'])
    unmount_device(device)

def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=str, help='Source media package')
    parser.add_argument('--device', type=str, help='Destination device')
    parser.add_argument('--file-system', dest='file_system', type=str, default='fat32', help='File system, fat32 or ntfs (default: fat32)')
    return parser.parse_args()


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


if __name__ == "__main__":
    configure_logging()

    args = parse_command_line()
    source_directory = MEDIA_PACKAGES_PATH + args.package

    media_package = {}
    with open(source_directory + '/.package.json') as json_file:
        media_package = json.load(json_file)

    format_media(args.device, args.file_system)
    copy_directory(source_directory, args.device)
