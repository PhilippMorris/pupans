#!/bin/bash

export PATH=$PATH:/usr/sbin

(/opt/eventlog/testconnection.py --ignorentp 2>&1 | /usr/local/bin/prefixwithtimestamp.sh) >> /var/log/testconnection.log