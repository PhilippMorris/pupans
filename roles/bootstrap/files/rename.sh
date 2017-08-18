#!/bin/bash

#
# Renane machine to its MAC address
#

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

MY_DIR=`dirname $0`

# Find primary NIC
PRIMARY_NIC=$(ip route get 8.8.8.8 | head -1 | cut -d' ' -f5)

# Set hostname to station<MAC>
NEWHOSTNAME=station`ifconfig $PRIMARY_NIC|awk '/HWaddr/ {print $5}'|sed 's/://g'`

echo "Changing hostname to $NEWHOSTNAME"
echo $NEWHOSTNAME > /etc/hostname
hostname $NEWHOSTNAME

echo "Adding 127.0.1.1 $NEWHOSTNAME to /etc/hosts"
$MY_DIR/../tools/hosts.sh remove ubuntu
$MY_DIR/../tools/hosts.sh remove template
$MY_DIR/../tools/hosts.sh remove station.*

if [ "$1" != "" ]; then
	NEWDOMAIN=".$1"
	$MY_DIR/../tools/hosts.sh add "$NEWHOSTNAME$NEWDOMAIN $NEWHOSTNAME" 127.0.1.1
else
	$MY_DIR/../tools/hosts.sh add $NEWHOSTNAME 127.0.1.1
fi
