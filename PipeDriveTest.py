# import boto3
# import botocore
import json
import requests
import csv
import sys

# ACCESS_KEY = 'xxx'
# SECRET_KEY = '​​xxx'

# s3 = boto3.client('s3',
#     aws_access_key_id=ACCESS_KEY,
#     aws_secret_access_key=SECRET_KEY)

# try:
#     deals_csv = s3.download_file('pdw-export.alpha', 'deals.csv.gz', 'test_tasks/deals.csv.gz')
# except botocore.exceptions.ClientError as e:
#     if e.response['Error']['Code'] == "404":
#         print("The object does not exist.")
#     else:
#         raise


def create_deal(payload):

    api_url = '{}deals?api_token={}'.format(api_url_base, api_token)

    response = requests.post(api_url, headers=headers,  data=payload)
    # print(response.json())

    if response.status_code == 201:
        id = response.json()["data"]["id"]
        print("Successfully created deal: {}".format(id))
        return id
    else:
        return json.loads(response.content)
    
def update_deal(deal_id, payload):
    
    api_url = '{}deals/{}?api_token={}'.format(api_url_base, deal_id, api_token)

    response = requests.put(api_url, headers=headers,  data=payload)
    # print(response.json())

    if response.status_code == 200:
        print("Successfully updated deal: {}".format(deal_id))
        return json.loads(response.content)
    else:
        return None

def delete_deal(deal_id):

    api_url = '{}deals/{}?api_token={}'.format(api_url_base, deal_id, api_token)

    response = requests.delete(api_url, headers=headers,  data=payload)
    # print(response.json())

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return None


### Script starts from here ######
if __name__ == '__main__':

    file_path = sys.argv[1] # 'C:\\Users\\rc\\Desktop\\deals.csv'
    api_token = sys.argv[2] # 'a0db207d7780a46a246b8a24f828736b8dcf4435'
    api_url_base = 'https://api.pipedrive.com/v1/'
    headers = {'Accept': 'application/json'}

    try:
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    payload = {"title": row["title"], "currency": row["currency"], "value": row["value"], "status": row["status"]  }
                    deal_id = create_deal(payload)
                    new_value = float(row["value"]) * 2
                    transformed_payload = {"value": new_value}
                    update_deal(deal_id, transformed_payload)
                    line_count += 1
            print(f'Processed {line_count} lines.')
    except IOError as e:
        print ("Could not read file:{}".format(e.strerror))
        sys.exit()
