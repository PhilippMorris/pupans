import logging
import azure.servicebus as sb
import azure

from bson.json_util import dumps

__author__ = 'aluetjen'


class AzureServiceBusGateway:
    namespace = ''
    key = ''
    issuer = ''

    def __init__(self):
        self.log = logging.getLogger("AzureServiceBusGateway")
        self.bus_service = sb.ServiceBusService(service_namespace=AzureServiceBusGateway.namespace,
                                                account_key=AzureServiceBusGateway.key,
                                                issuer=AzureServiceBusGateway.issuer)

    def upload_event(self, event):
        event_serialized = dumps(event)
        msg = sb.Message(event_serialized)
        topic = event['Type'].lower()

        try:
            self.bus_service.send_topic_message(topic, msg)
        except azure.WindowsAzureMissingResourceError:
            self.log.warning("Topic {0} not available for event {1}.".format(topic, event['_id']))