#!/bin/bash

maxdelay="$1"
[[ "$maxdelay" == "" ]] && maxdelay=$((3*60))

delay=$(($RANDOM%maxdelay))
echo "Delaying for $delay minutes."
/sbin/shutdown -r "+$delay" &
