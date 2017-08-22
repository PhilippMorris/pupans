#!/bin/bash

export PATH=$PATH:/usr/sbin

#Gracefully terminate any running events.py process
h=$(pgrep -f events.py)
if [[ -n $h ]]; then
  kill $h
  count=0
  while [[ -n $h && $x -lt 5 ]]; do
    sleep 1
	((count++))
    h=$(pgrep -f events.py)
  done
fi

#Forcefully terminate any running events.py process
h=$(pgrep -f events.py)
if [[ -n $h ]]; then
  kill -9 $h
fi
rm -f /var/run/events.pid

TESTRESULT=$(/opt/eventlog/testconnection.py)

if [ "$?" != "1" ]
then
	/opt/eventlog/events.py add 'Connected' "$TESTRESULT"
else
	/opt/eventlog/events.py add 'Warning' "Internet connectivity lost: $TESTRESULT"
fi

# Probably no need to even try to post the event log because the internet connection seems to be unavailable. But who knows... no harm in trying...
/opt/eventlog/events.py postazure
/opt/eventlog/events.py post

