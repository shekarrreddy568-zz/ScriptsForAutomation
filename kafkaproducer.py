#!/usr/bin/python

import requests
import json

url = "http://hadoop-fra-5.intern.beon.net:8082/topics/my_topic"
headers = {
    "Content-Type" : "application/vnd.kafka.json.v2+json"
    }
 # Create one or more messages
for i in range(100): 
    payload = {
        "records": [
            {
            "key": "key {}".format(i),
            "value": "message {}".format(i)
            } ]}
    # Send the message
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    if r.status_code != 200:
        print ("Status Code: {}".format(r.status_code))
        print (r.text)
    else:
        print (r.text)