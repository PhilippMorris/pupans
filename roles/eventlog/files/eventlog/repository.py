import datetime
import logging
import re
import socket
import pymongo as mdb

__author__ = 'aluetjen'


class MongoDbRepository:
    host = "localhost"
    port = 27017

    def __init__(self, collection=None, clock=None):

        self.hostname = socket.getfqdn()
        self.mac = self._get_mac_from_hostname(self.hostname)

        self.logger = logging.getLogger("EventRepository")
        self.clock = clock if clock is not None else datetime.datetime.utcnow

        if collection is None:
            client = mdb.MongoClient(MongoDbRepository.host, MongoDbRepository.port)
            db = client.AppChord
            self.__collection = db.Events

            self.__collection.ensure_index(u'UploadState')
        else:
            self.__collection = collection

    def _get_mac_from_hostname(self, hostname):
        match = re.match('^[^\\.]*([^\\.]{12})(\\..*)?', hostname)

        if match is not None:
            return match.group(1)
        else:
            return None

    def add(self, event_type, event_details, event_date=None):

        if event_date is None:
            event_date = self.clock()

        event = {'Type': event_type,
                 'Details': event_details,
                 'StationName': self.hostname,
                 'Date': event_date,
                 'MacAddress': self.mac}

        self.__collection.insert(event)

        self.logger.info("Added event id={4} type={0} details={1} station={2} mac={3}".format(
            event_type, event_details, self.hostname, self.mac, event[u'_id']))

    def update(self, event):
        self.__collection.update({u'_id': event[u'_id']}, event)
        self.logger.info("Updated event id={0}".format(event[u'_id']))

    def find(self, query):
        return self.__collection.find(query)

    def delete_all(self):
        self.__collection.remove()
        self.logger.info("Discarded all events.")

    def any(self):
        return self.__collection.find()

    def without_upload_state(self):
        return self.__collection.find({u'UploadState': {u'$not': {u'$exists': u'false'}}})