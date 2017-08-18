#!/bin/bash
# Ensure that the SSH tunnel is run using the updated configuration
# if it is supposed to be running in the current runlevel.

runlevel | grep -q "[$1]"

if [ $? = 0 ];
then
	stop sshtunnel
	start sshtunnel
fi
