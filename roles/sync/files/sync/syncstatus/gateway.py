__author__ = 'lolsen'

from bson.json_util import dumps
import logging
import requests
import azure.servicebus as sb
import azure

LOGGER = logging.getLogger("gateway")


class HttpRestGateway:
    url = "http://localhost/api/syncstatus"
    user = None
    password = None
    ssl_insecure = False

    def upload_syncstatus(self, syncstatus):
        syncstatus_serialized = dumps(syncstatus)
        headers = {'content-type': 'application/json'}
        auth = None
        verify = not HttpRestGateway.ssl_insecure

        if HttpRestGateway.user is not None:
            auth=(HttpRestGateway.user,HttpRestGateway.password)

        r = requests.post(HttpRestGateway.url, auth=auth, data=syncstatus_serialized, headers=headers, verify=verify)

        if (not r.ok) or (200 > r.status_code > 299):
            raise IOError(("Failed to upload sync status to server. OK %s HTTP response code: %d" % (r.ok, r.status_code)))


class AzureServiceBusGateway:
    namespace = ''
    key = ''
    issuer = ''

    def __init__(self):
        self.log = logging.getLogger("AzureServiceBusGateway")
        self.bus_service = sb.ServiceBusService(service_namespace=AzureServiceBusGateway.namespace,
                                                account_key=AzureServiceBusGateway.key,
                                                issuer=AzureServiceBusGateway.issuer)

    def upload_syncstatus(self, syncstatus):
        syncstatus_serialized = dumps(syncstatus)
        msg = sb.Message(syncstatus_serialized)
        topic = "syncstatus"

        self.bus_service.send_topic_message(topic, msg)


class EchoGateway:

    def upload_syncstatus(self, syncstatus):
        syncstatus_serialized = dumps(syncstatus)

        LOGGER.info("%s" % (syncstatus_serialized))
