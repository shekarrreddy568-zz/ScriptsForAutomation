from boto3.session import Session
import boto3
import os
import json
import requests
import botocore

ACCESS_KEY = 'xxx'
SECRET_KEY = '​​xxx'

s3 = boto3.client('s3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY)

try:
    deals_csv = s3.download_file('pdw-export.alpha', 'deals.csv.gz', 'test_tasks/deals.csv.gz')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise

api_token = 'a0db207d7780a46a246b8a24f828736b8dcf4435'
headers = {'Accept': 'application/json'}

def create_deal():

    api_url = 'https://api.pipedrive.com/v1/deals?api_token={}'.format(api_token)
    payload = { "title": "test3" }

    response = requests.post(api_url, headers=headers,  data=payload)
    print(response.json())

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return None
    
def update_deal():
    
    deal_id = 6
    api_url = 'https://api.pipedrive.com/v1/deals/{}?api_token={}'.format(deal_id, api_token)
    payload = { "currency": "INR" }

    response = requests.put(api_url, headers=headers,  data=payload)
    print(response.json())

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return None