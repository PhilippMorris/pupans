import logging
from bson.json_util import dumps

__author__ = 'aluetjen'


class EchoGateway:
    def __init__(self):
        self.log = logging.getLogger("EchoGateway")

    def upload_event(self, event):
        event_transformed = event.copy()
        event_transformed[u'_id'] = str(event_transformed[u'_id'])
        event_serialized = dumps(event_transformed)

        self.log.info("{0}: {1}".format(event[u'_id'], event_serialized))