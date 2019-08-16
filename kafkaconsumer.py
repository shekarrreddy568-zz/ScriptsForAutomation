 #!/usr/bin/python
import requests
import base64
import json
import sys

# Base URL for interacting with REST server
baseurl = "http://hadoop-fra-5.intern.beon.net:8082/consumers/consumer_group3"

# Create the Consumer instance
print ("Creating consumer instance")
payload = {
    "format": "json"
    }
headers = {
 "Content-Type" : "application/vnd.kafka.json.v2+json"
 }

r = requests.post(baseurl, data=json.dumps(payload), headers=headers)

if r.status_code != 200:
    print ("Status Code: " + str(r.status_code))
    print (r.text)
    sys.exit("Error thrown while creating consumer")
else:
    print ("instance: {}".format(r.text))

# Base URI is used to identify the consumer instance
base_uri = r.json()["base_uri"]

print("base_uri: {}".format(base_uri))


### subscribe

headers = {
 "Content-Type" : "application/vnd.kafka.v2+json"
 }

payload = {"topics":["my_topic"]}

r = requests.post(baseurl + "/subscription", data=json.dumps(payload), headers=headers)

# if r.status_code != 200:
#     print ("Status Code: " + str(r.status_code))
#     print (r.text)
#     sys.exit("Error thrown while subscribing topic")
# else:
print (r.text)


# Get the message(s) from the Consumer
headers = {
    "Accept" : "application/vnd.kafka.json.v2+json"
    }

 # Request messages for the instance on the Topic
r = requests.get(base_uri + "/records", headers=headers, timeout=20)

if r.status_code != 200:
    print ("Status Code: " + str(r.status_code))
    print (r.text)
    sys.exit("Error thrown while getting message")
else:
    print (r.text)

 # Output all messages
for message in r.json():
    if message["key"] is not None:
        print ("Message Key:" + message["key"])
    print ("Message Value:" + message["value"])

    # When we're done, delete the Consumer
# headers = {
#     "Accept" : "application/vnd.kafka.v2+json, application/vnd.kafka+json, application/json"
#     }

# r = requests.delete(base_uri, headers=headers)

# if r.status_code != 204:
#     print ("Status Code: " + str(r.status_code))
#     print (r.text)