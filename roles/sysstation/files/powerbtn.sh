#!/bin/sh
# /etc/acpi/powerbtn.sh
# Initiates a shutdown when the power putton has been
# pressed.

# Send event to nodejs kiosk on power button.
# Use 'python /opt/powercontrol.py --poweroff' or 'python /opt/powercontrol.py --reboot'.

python /opt/kiosk/send_event.py --name power-button



