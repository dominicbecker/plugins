#!/usr/bin/env python
import sys
import requests
import json
import socket

services = ['HBase,name=*', 'RegionServer,name=*']

excludes = []
    
metrics = {}
node_data = {}

for s in services:
    URL = 'http://%s:60030/jmx?qry=hadoop:service=%s' % (socket.getfqdn(), s)
    try:
        resp = requests.get(URL).json()['beans']
        for i in range(len(resp)):
            for k, v in resp[i].iteritems():
                if k.lower() not in excludes:
                    metrics[k] = v

    
    except Exception, e:
        print "connection failed: %s" % e
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output

