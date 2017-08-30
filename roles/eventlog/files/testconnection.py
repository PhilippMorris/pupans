#!/usr/bin/python

import sh
import sys
import os
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--ignorentp', dest="ignore_ntp", action='store_true', default=False)

    args = parser.parse_args()

    connection_results = {('api.ar.appchord.com', 443): '?', ('www.google.com', 80): '?', ('tunnel.basechord.com', 22): '?'}

    for key in connection_results.keys():
        result = sh.nc('-z', '-w3', key[0], key[1], _ok_code=(0,1))

        if result.exit_code == 0:
            connection_results[key] = 'OK'
        else:
            connection_results[key] = 'Failed'

        print('PROBE: {0}:{1} {2}'.format(key[0], key[1], connection_results[key]))

    if not os.path.exists('/opt/eventlog/testconnection.ignorentp') and not args.ignore_ntp:
        result = sh.ntpdate('pool.ntp.org', _ok_code=(0,1))

        if result.exit_code == 0:
            ntp_available = True
            ntp_status = "OK"
        else:
            ntp_available = False
            ntp_status = "Failed"

    else:
        ntp_available = None
        ntp_status = "Skipped"

    print('PROBE: pool.ntp.org:123 {0}'.format(ntp_status))

    if connection_results[('www.google.com', 80)] == 'OK':
        internet_connectivity = True

        if any(connection != 'OK' for connection in connection_results.itervalues()) or ntp_available == False:
            sys.exit(2)
        else:
            sys.exit(0)
    else:
        internet_connectivity = False
        sys.exit(1)



