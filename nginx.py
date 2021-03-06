#!/usr/bin/env python
import re
import requests
import sys
import json
import os
from datetime import datetime

URL = 'http://127.0.0.1/nginx_status'
TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'dl-nginx.json'
DATA = {}
TIMESTAMP = datetime.now().strftime('%s')


def tmp_file():
    # Ensure the dataloop tmp dir is available
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)

def get_cache():
    with open(TMPDIR + '/' + TMPFILE, 'r') as json_fp:
        try:
            json_data = json.load(json_fp)
        except:
            print "not a valid json file. rates calculations impossible"
            json_data = []
    return json_data

def write_cache(cache):
    with open(TMPDIR + '/' + TMPFILE, 'w') as json_fp:
        try:
            json.dump(cache, json_fp)
        except:
            print "unable to write cache file, future rates will be hard to calculate"

def cleanse_cache(cache):
    # keep the cache at a max of 1 hour of data
    while (int(TIMESTAMP) - int(cache[0]['timestamp'])) >= 3600:
        cache.pop(0)
    # keep the cache list to 120
    while len(cache) >= 120:
        cache.pop(0)
    return cache

def calculate_rates(data_now, json_data, rateme):
    # Assume last value gives up to an hour's worth of stats
    # ie 120 values stored every 30 secs
    # pop the first value off our cache and caluculate the rate over the timeperiod
    if len(json_data) > 1:
        history = json_data[0]
        seconds_diff = int(TIMESTAMP) - int(history['timestamp'])
        rate_diff = float(data_now[rateme]) - float(history[rateme])
        data_per_second = "{0:.2f}".format(rate_diff / seconds_diff)

        return data_per_second

def get_nginx_status():
    try:
        resp = requests.get(URL)
    except:
        print "connection failed"
        sys.exit(2)

    data = resp.text
    result = {}

    match1 = re.search(r'Active connections:\s+(\d+)', data)
    match2 = re.search(r'\s*(\d+)\s+(\d+)\s+(\d+)', data)
    match3 = re.search(r'Reading:\s*(\d+)\s*Writing:\s*(\d+)\s*''Waiting:\s*(\d+)', data)

    if not match1 or not match2 or not match3:
        raise Exception('Unable to parse %s' % URL)
        sys.exit(2)

    result['connections'] = int(match1.group(1))
    result['accepted'] = int(match2.group(1))
    result['handled'] = int(match2.group(2))
    result['requests'] = int(match2.group(3))
    result['reading'] = int(match3.group(1))
    result['writing'] = int(match3.group(2))
    result['waiting'] = int(match3.group(3))

    return result


# Flow
# Ensure the tmp dir and file exist
tmp_file()

# Get our cache of data
json_data = get_cache()
#print json_data
if len(json_data) > 0:
    json_data = cleanse_cache(json_data)

# get the current ngin status
result = get_nginx_status()

rate = calculate_rates(result, json_data, 'requests')
if rate is not None:
    result['requests_per_second'] = rate

# append to the cache and write out for the next pass
dated_result = result
dated_result['timestamp'] = TIMESTAMP
json_data.append(dated_result)
write_cache(json_data)

# Finally nagios exit with perfdata
perf_data = "OK | "
for k, v in result.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)
print perf_data
sys.exit(0)
