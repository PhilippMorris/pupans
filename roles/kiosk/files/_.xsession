#!/usr/bin/env bash

logger Starting Xsession for Kiosk mode.

#Disable mouse right-click
xmodmap -e "pointer = 1 2 99"

matchbox-window-manager &

while true; do

	#Enable NumLock
	/usr/bin/numlockx on

	# Discard any Chromium preferences
	rm -rf ~/.config/chromium
	rm -rf ~/.config/google-chrome
	rm -rf ~/.cache

	google-chrome --no-first-run --noerrdialogs --disable-infobars --kiosk http://localhost/index.html;

	logger Restarting Kiosk browser.

	sleep 1s;
done
