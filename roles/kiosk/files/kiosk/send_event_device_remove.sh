#!/bin/bash
/usr/bin/python /opt/kiosk/send_event.py --name device-remove --jsondata "{\"id\":\"$1\"}"