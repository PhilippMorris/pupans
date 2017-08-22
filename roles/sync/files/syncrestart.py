#!/usr/bin/python
from time import sleep
import sys
import os
import re
import signal
import subprocess
import argparse
import datetime
import json


def stop(signum, frame):
    print("SyncRestart wrapper received stop event...")


class ProcessStillRunning(Exception):
    pass


def kill_using(command, send_signal, delay, attempts):
    my_pid = os.getpid()

    check_count = 0
    waiting_sigterm = True
    while waiting_sigterm and check_count < attempts:
        waiting_sigterm = False
        ps_output = subprocess.check_output(['ps', '-eo', 'pid,command']).decode('ascii')
        for process_line in ps_output.splitlines():
            process_match = re.match(r'\s*(\d+)\s+{command}'.format(**locals()), process_line)
            if process_match is not None:
                matched_pid = int(process_match.group(1))

                if matched_pid == my_pid:
                    continue

                waiting_sigterm = True
                print("Killing {matched_pid}...".format(**locals()))
                os.kill(matched_pid, send_signal)

        if waiting_sigterm:
            sleep(delay)
            check_count += 1

    if check_count == attempts:
        raise ProcessStillRunning()


def kill_command(command):
    # Attempt regular shutdown using SIGTERM and wait 5 seconds
    kill_using(command, 5, signal.SIGTERM, 2)

    # Attempt another SIGTERM and wait longer this time
    kill_using(command, 5, signal.SIGTERM, 30)

    # Forcefully kill now, since the process seems to hang
    kill_using(command, 5, 9, 30)


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def load_last_rescan():
    filename = os.path.join(get_script_path(), 'syncrestart_last_rescan.json')
    if os.path.isfile(filename):
        with open(filename, 'r') as infile:
            last_rescan = json.load(infile)
            last_rescan["date"] = datetime.datetime.strptime(last_rescan["date"], "%Y-%m-%d").date()
            return last_rescan
    else:
        return None


def save_last_rescan():
    filename = os.path.join(get_script_path(), 'syncrestart_last_rescan.json')
    last_rescan = {
        "date": datetime.datetime.now().date().isoformat()
    }
    with open(filename, 'w') as outfile:
        json.dump(last_rescan, outfile)


def erase_torrent_states(torrents_directory):
    print("Clearing torrent states to force a rescan.")
    os.chdir(torrents_directory)
    files = [ file for file in os.listdir(".") if file.endswith(".torrent") or file.endswith(".torrent.state") ]
    for file in files:
        os.remove(file)
    save_last_rescan()


def trigger_torrent_rescan(torrents_directory, force_rescan, auto_rescan_days):
    last_rescan = load_last_rescan()
    if force_rescan or last_rescan is None:
        erase_torrent_states(torrents_directory)
    else:
        date_diff = abs(datetime.datetime.now().date() - last_rescan["date"]).days
        if date_diff >= auto_rescan_days:
            erase_torrent_states(torrents_directory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop', action='store_true', help="Only stop, don't restart the sync script.")
    parser.add_argument('--seeder', type=str, default='https://seeder.basechord.com', help='URL of the seeder.')
    parser.add_argument('--speed', type=str, default='default', help='Speed of download: default, low, or high.')
    parser.add_argument('--seederuser', dest='seeder_user', type=str, default='p2p', help='User for authenticating to the seeder.')
    parser.add_argument('--seederpassword', dest='seeder_password', type=str, default='AppCh0rd', help='Password for authenticating to the seeder.')
    parser.add_argument('--rescandays', type=int, default=90, help='How frequently to rehash existing data for torrents.')
    parser.add_argument('--forcerescan', action='store_true', help='Force rehash existing data for torrents.')
    parser.add_argument('--firstpriority', dest='first_priority', type=str, help='Torrent(s) that should be downloaded first. If any part of the torrent name matches the string specified, it will be downloaded first.')
    parser.add_argument('--ignore', dest='ignore', type=str, help='Torrent(s) that should be ignored. If any part of the torrent name matches the string specified, it will be skipped.')

    parser.add_argument('--branch', type=str, default='master', help='Branch for torrent files: lab, canary, canary2 or production.')


    args = parser.parse_args()

    port = 443
    path = ''
    if args.speed != 'default':
        path = args.speed + '-speed'

    sync_content_script = '/usr/bin/python /opt/sync/synccontent.py'
    sync_content_command = sync_content_script + ' --torrents /usr/share/p2pclient/torrents/ --downloads /usr/share/p2pclient/download/ --seeder "{0}" --port "{1}" --path "{2}" --seederuser "{3}" --seederpassword "{4}" --firstpriority "{5}"'.format(args.seeder, port, path, args.seeder_user, args.seeder_password, args.first_priority)
    sync_torrents_script = '/usr/bin/python /opt/sync/synctorrents.py'
    sync_torrents_command = sync_torrents_script + ' --torrents /usr/share/p2pclient/torrents/ --seeder "{0}" --port "{1}" --path "{2}" --seederuser "{3}" --seederpassword "{4}" --ignore "{5}" --branch "{6}"'.format(args.seeder, port, path, args.seeder_user, args.seeder_password, args.ignore, args.branch)

    # Kill any sync that might still be outstanding
    kill_command(sync_torrents_script)
    kill_command(sync_content_script)

    trigger_torrent_rescan('/usr/share/p2pclient/torrents/', args.forcerescan, args.rescandays)

    if not args.stop:
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)

        subprocess.call(sync_torrents_command, shell=True)
        subprocess.call(sync_content_command, shell=True)
