#!/bin/bash

# Writes the UTCOFFSET fact to /etc/facter/facts.d. This script is not executed
# as part of facter by intention. This "indirection" decouples potential issues
# of the GeoIP lookup and timezone calculation from the Puppet run. E.g. a GeoIP
# lookup and especially the public IP lookup can take quite a bit of time.

UTCOFFSET=`geolocate.py utcoffset 2>/dev/null`

if [ "$?" != "0" ] ; then
    UTCOFFSET=-6
fi

mkdir -p /opt/station/

cat >/opt/station/utcoffset.sh <<EOF
#!/bin/bash
echo "utcoffset=$UTCOFFSET"
EOF
chmod +x /opt/station/utcoffset.sh
