#!/usr/bin/env python3
#######
# AUTHOR: Engit Prabhat <john-e@github>
# LICENSE: MIT 
#######
# monkey-patch
import gevent.monkey
gevent.monkey.patch_all()

import gevent.pool
import gevent.queue

import sys
import re
import requests
import validators
from urllib.parse import urljoin

WORKER_COUNT = 10
URLREGEX = r"url\"\s*:\s*\"\/([^\"]+)\""

def getUrl(path):
    return urljoin(sys.argv[1]+'/', path.strip('/'))

tranvered = {}
pool = gevent.pool.Pool(WORKER_COUNT)
queue = gevent.queue.Queue()

def crawler():
    while 1:
        try:
            url = queue.get(timeout=0)
            print ('Fetching ... %s' % url)
            response = requests.get(url)

            if response.status_code == requests.codes.ok:
                # Extract some links to follow
                for link in re.findall(URLREGEX, response.text):
                    if link not in tranvered:
                        tranvered[link] = True
                        queue.put(getUrl(link))
            else:
                print('\x1b[0;30;41mFAILED\x1b[0m with %d ... %s' % (response.status_code, url))

        except gevent.queue.Empty:
            print ('queue empty')
            break

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('USAGE:\n\t%s <base_url> <entry_path>' % sys.argv[0])
        sys.exit(1)

    if validators.url(sys.argv[1]) != True:
        print('Invalid Url')
        sys.exit(1)

    queue.put(getUrl(sys.argv[2]))
    pool.spawn(crawler)

    while 1:
        if queue.empty() and pool.free_count() == WORKER_COUNT:
            print ('No more links left and nothing running')
            break

        for x in range(0, min(queue.qsize(), pool.free_count())):
            pool.spawn(crawler)
        gevent.sleep(0.1)

    # Wait for everything to complete
    pool.join()
