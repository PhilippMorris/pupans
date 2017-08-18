__author__ = 'lolsen'

import os
import subprocess
import logging
import datetime
import socket
import json

from syncstatus.gateway import HttpRestGateway

def getDirectorySize(dir):
    command = ['du', "-ksL", dir]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None)
    output = process.communicate()[0]
    directorySize = int(output.split()[0])
    # subtract the size of the root directory object itself
    directorySize -= 4
    return directorySize

def getSubdirectories(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]


class LocalMachine:
    def name(self):
        return socket.gethostname()


class Manager:
    MAX_INT = 2147483647

    def __init__(self, script_dir, downloads, gateway=None, local_machine=None):
        self.script_dir = script_dir
        self.downloads = downloads
        self.gateway = HttpRestGateway() if gateway is None else gateway
        self.local_machine = LocalMachine() if local_machine is None else local_machine
        self.log = logging.getLogger('Manager')

    def process(self):
        stationName = self.local_machine.name()
        dailyDownloadRateKB = self.getDailyDownloadRate()
        packageStatus = self.getPackageStatus()
        syncstatus = {
            "StationName": stationName,
            "DailyDownloadRateKB": dailyDownloadRateKB,
            "PackageStatus": packageStatus
        }
        self.gateway.upload_syncstatus(syncstatus)
        self.log.info("Uploaded sync status")

    def getDailyDownloadRate(self):
        dailyDownloadRate = None
        newDailyComplete = {
            "totalDownloadComplete": getDirectorySize(self.downloads),
            "date": datetime.datetime.now().date()
        }
        self.log.info("total download complete: {0} KB".format(newDailyComplete["totalDownloadComplete"]))

        #load previous daily complete data
        oldDailyComplete = self.loadDailyComplete()
        if (oldDailyComplete is not None):
            dateDiff = abs(newDailyComplete["date"] - oldDailyComplete["date"]).days
            completeDiff = newDailyComplete["totalDownloadComplete"] - oldDailyComplete["totalDownloadComplete"]
            self.log.info("Days since daily download rate was last reported: {0}".format(dateDiff))
            self.log.info("Kilobytes downloaded since last reported: {0}".format(completeDiff))
            if dateDiff > 0:
                dailyDownloadRate = int(completeDiff / dateDiff)
                # Only update the total download complete if it's been a day since reporting the daily download rate
                self.saveDailyComplete(newDailyComplete)
        else:
            # save the total download complete to a file for future reference
            self.saveDailyComplete(newDailyComplete)

        return dailyDownloadRate

    def loadDailyComplete(self):
        filename = os.path.join(self.script_dir, 'syncstatus_daily_complete.json')
        if os.path.isfile(filename):
            with open(filename, 'r') as infile:
                oldDailyComplete = json.load(infile)
                oldDailyComplete["date"] = datetime.datetime.strptime(oldDailyComplete["date"], "%Y-%m-%d").date()
                return oldDailyComplete
        else:
            return None

    def saveDailyComplete(self, dailyComplete):
        filename = os.path.join(self.script_dir, 'syncstatus_daily_complete.json')
        dailyComplete["date"] = dailyComplete["date"].isoformat()
        with open(filename, 'w') as outfile:
            json.dump(dailyComplete, outfile)

    def getPackageStatus(self):
        packageStatus = {}
        downloadDirs = getSubdirectories(self.downloads)
        for dir in downloadDirs:
            downloaddirectory = os.path.join(self.downloads, dir)
            completefile = os.path.join(downloaddirectory, ".complete")
            if os.path.isfile(completefile):
                self.log.info("{0} is complete.".format(dir))
                packageStatus[dir] = self.MAX_INT
            else:
                packageStatus[dir] = getDirectorySize(downloaddirectory)
        return packageStatus
