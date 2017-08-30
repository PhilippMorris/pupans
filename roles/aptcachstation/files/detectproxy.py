import socket
import os
import sys
from random import randint
from time import sleep
# usage: detectproxy.py puppetmaster 3142
try:
    apt_cacher = sys.argv[1]
    port = sys.argv[2]

    sleep(randint(5,60))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    s.connect((apt_cacher, int(sys.argv[2])))
#    print "connected"
    proxy = 'Acquire::http { Proxy \\"http://'+apt_cacher+':'+str(port)+'\\"; };'
    echoproxy = 'echo "' + proxy + '" > /etc/apt/apt.conf.d/00proxy '
    os.system(echoproxy)
    os.system("echo 'Acquire::http::Proxy { deb.nodesource.com DIRECT; };' >> /etc/apt/apt.conf.d/00proxy ")
    os.system("echo 'Acquire::http::Proxy { downloads-distro.mongodb.org DIRECT; };' >> /etc/apt/apt.conf.d/00proxy ")
#    os.system("echo 'Acquire::http::Proxy { apt.dockerproject.org DIRECT; };' >> /etc/apt/apt.conf.d/00proxy ")
    s.close()
except socket.error as e:
    os.system("rm -rf /etc/apt/apt.conf.d/00proxy")
#    print "no connection"
