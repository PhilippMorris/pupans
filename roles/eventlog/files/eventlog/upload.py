import datetime
import logging
from eventlog.repository import MongoDbRepository
from eventlog.gateway_echo import EchoGateway
from eventlog.gateway_rest import HttpRestGateway

__author__ = 'aluetjen'


class EventUpload:
    def __init__(self, events=None, gateway=None, clock=None, simulation=False):
        self.events = MongoDbRepository() if events is None else events

        if gateway is None:
            if simulation:
                self.gateway = EchoGateway()
            else:
                self.gateway = HttpRestGateway() if gateway is None else gateway
        else:
            self.gateway = gateway

        self.clock = datetime.datetime.utcnow if clock is None else clock
        self.logger = logging.getLogger("EventUpload")

        self.simulation = simulation
        self.max_event_age_hours = 24 * 7

    def upload(self):
        for event in self.events.without_upload_state():
            try:
                if self.is_outdated(event):
                    self.process_outdated_event(event)
                    continue

                self.upload_event(event)
            except IOError as exception:
                self.logger.error("Failed to upload id=%s" % (event[u'_id']))
                self.logger.error(exception)
                continue

            self.logger.info("Uploaded id=%s" % (event[u'_id']))

    def upload_event(self, event):
        event[u'Uploaded'] = self.clock()
        event[u'UploadState'] = 'Uploaded'

        self.gateway.upload_event(event)

        if not self.simulation:
            self.events.update(event)

    def process_outdated_event(self, event):
        event[u'UploadState'] = 'Outdated'

        if not self.simulation:
            self.events.update(event)

        self.logger.error('Skipping event id={0} since it is too old and considered a poison event.'.
              format(event['_id']))

    def is_outdated(self, session):
        lifetime = (self.clock() - session[u'Date'])
        return lifetime > datetime.timedelta(hours=self.max_event_age_hours)