#!/bin/bash

#
# Renane machine to its MAC address
#

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Find primary NIC
PRIMARY_NIC=$(ip route get 8.8.8.8 | head -1 | cut -d' ' -f5)

# Set hostname to station<MAC>
NEWHOSTNAME=station`ifconfig $PRIMARY_NIC|awk '/HWaddr/ {print $5}'|sed 's/://g'`

echo "Changing hostname to $NEWHOSTNAME"
echo $NEWHOSTNAME > /etc/hostname
hostname $NEWHOSTNAME

echo "Adding 127.0.1.1 $NEWHOSTNAME to /etc/hosts"
/usr/local/bin/hosts.sh remove ubuntu
/usr/local/bin/hosts.sh remove template
/usr/local/bin/hosts.sh remove station.*

NEWDOMAIN=".ar.appchord.com"
/usr/local/bin/hosts.sh add "$NEWHOSTNAME$NEWDOMAIN $NEWHOSTNAME" 127.0.1.1
