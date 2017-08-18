#! /bin/sh

#
# Set the 'Kiosk mode' GRUB menu entry as default.
# The machine will autologin and start Nodm with Chromium.
#

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

sed -ie s/GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/g /etc/default/grub
grub-set-default "Kiosk mode"
update-grub
