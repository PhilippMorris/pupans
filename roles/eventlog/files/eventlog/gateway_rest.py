from bson.json_util import dumps
import requests

__author__ = 'aluetjen'


class HttpRestGateway:
    url = "http://localhost/api/stationevent"
    user = None
    password = None
    ssl_insecure = False

    def upload_event(self, event):
        event_transformed = event.copy()
        event_transformed[u'_id'] = str(event_transformed[u'_id'])
        event_serialized = dumps(event_transformed)

        headers = {'content-type': 'application/json'}
        auth = None
        verify = not HttpRestGateway.ssl_insecure

        if HttpRestGateway.user is not None:
            auth = (HttpRestGateway.user, HttpRestGateway.password)

        r = requests.post(HttpRestGateway.url, auth=auth, data=event_serialized, headers=headers, verify=verify, timeout=10)

        if (not r.ok) or (200 > r.status_code > 299):
            raise IOError(("Failed to upload event to server. OK %s HTTP response code: %d" % (r.ok, r.status_code)))