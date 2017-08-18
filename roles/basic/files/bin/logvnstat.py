#!/usr/bin/python
import sys
import xml.etree.ElementTree as ET

# Run using: vnstat --xml | ./logvnstat.py > /var/log/cronjobs/vnstat.log
if __name__ == '__main__':
    if len(sys.argv) == 2:
        vnstat_tree = ET.parse(sys.argv[1])
    else:
        vnstat_tree = ET.parse(sys.stdin)

    for interface in vnstat_tree.iter('interface'):
        interface_name = interface.get('name')

        for hour in interface.findall('./traffic/hours/hour'):
            date = hour.find('date')
            date_year = date.find('year').text
            date_month = date.find('month').text
            date_day = date.find('day').text
            date_hour = int(hour.get('id'))
            rx = int(hour.find('rx').text) * 1024
            tx = int(hour.find('tx').text) * 1024
            print('{0}-{1}-{2} {3:02d}:00:00,000 if={6}, rx={4}, tx={5}'.format(
                date_year, date_month, date_day, date_hour, rx, tx, interface.get('id')))