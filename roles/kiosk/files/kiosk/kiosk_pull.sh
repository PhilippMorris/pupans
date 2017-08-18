#!/bin/bash
if [ "$1" == "" ] ; then
    echo "Usage:"
    echo "kiosk_pull.sh <repository>"
else
    mkdir -p /var/www/kiosk
    cd /var/www/kiosk
    git rev-parse --is-inside-work-tree > /dev/null
    if [ $? -eq 0 ] ; then
        git fetch
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse @{u})
        if [ "$LOCAL" == "$REMOTE" ] ; then
            echo "Kiosk is already up-to-date."
        else
            echo "Pulling Kiosk update..."
            service kiosk stop
            git reset --hard origin/$1
            git pull
            npm install --unsafe-perm
            service kiosk start
            /usr/bin/killall chrome
            echo "Complete."
        fi
    else
        echo "Cloning Kiosk..."
        service kiosk stop
        rm -rf *
        git clone -b $1 https://bchodbot:Pf4EZGEu@github.com/BaseChord/KioskDistribution.git .
        npm install --unsafe-perm
        service kiosk start
        /usr/bin/killall chrome
        echo "Complete."
    fi
fi
