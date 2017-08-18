import requests
import json


class Sender(object):
    def __init__(self):
        self.post_url = "http://localhost:80/event/"

    def send(self, name, data):
        url = self.post_url + name
        headers = {'content-type': 'application/json'}
        auth = None
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers, verify=False)
        if (not r.ok) or (200 > r.status_code > 299):
            raise IOError(("Failed to upload session to server. OK %s HTTP response code: %d" % (r.ok, r.status_code)))