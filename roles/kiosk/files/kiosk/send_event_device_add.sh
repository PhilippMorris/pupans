#!/bin/bash
bytes=$(blockdev --getsize64 /dev/$1)
/usr/bin/python /opt/kiosk/send_event.py --name device-add --jsondata "{\"id\":\"$1\", \"type\": \"$2\", \"size\":\"$bytes\"}"