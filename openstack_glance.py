#!/usr/bin/env python
import sys
import os
import requests
from keystoneclient.v2_0 import client
from keystoneclient import exceptions

OS_USERNAME = ""
OS_TENANT_NAME = ""
OS_PASSWORD = ""
OS_AUTH_URL = "http://keystone.domain.com:5000/v2.0/"

def _get_keystone_token():
	token_id=[]
	try:
    		c_keystone = client.Client(username=OS_USERNAME,
    		                           tenant_name=OS_TENANT_NAME,
                  	                   password=OS_PASSWORD,
                  	                   auth_url=OS_AUTH_URL,
                  	                   insecure=True)
    		if not c_keystone.authenticate():
        		raise Exception("Authentication failed")
    		
	except Exception, e:
	    sys.exit(2)
	
	token_id.append(c_keystone.auth_token)
	token_id.append(c_keystone.tenant_id)
	return token_id

auth_token_id_nova=_get_keystone_token()

headers = { "X-Auth-Project-Id": OS_TENANT_NAME, "Content-Type": "application/json", "X-Auth-Token": auth_token_id_nova[0] }
try:
    resp = requests.get('http://127.0.0.1:9292/v1/images/detail', headers=headers).json()
except Exception, e:
    print "glance is down!"
    sys.exit(2)

print "OK | image_count=%s;;;;" % len(resp['images'])
