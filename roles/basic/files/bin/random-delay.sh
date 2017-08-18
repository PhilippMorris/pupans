#!/bin/bash

maxdelay="$1"
[[ "$maxdelay" == "" ]] && maxdelay=$((60*60))

delay=$(($RANDOM%maxdelay))
echo "Delaying for $delay seconds."
sleep $delay