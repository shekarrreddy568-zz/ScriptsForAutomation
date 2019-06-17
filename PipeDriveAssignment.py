import json
import requests
import csv
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

def create_deal(session, payload):

    api_url = '{}deals?api_token={}'.format(api_url_base, api_token)

    response = requests.post(api_url, headers=headers,  data=payload)
    # print(response.json())

    if response.status_code == 201:
        id = response.json()["data"]["id"]
        print("Successfully created deal: {}".format(id))
        return id
    else:
        return json.loads(response.content)
    
def update_deal(session, deal_id, payload):
    
    api_url = '{}deals/{}?api_token={}'.format(api_url_base, deal_id, api_token)

    response = requests.put(api_url, headers=headers,  data=payload)
    # print(response.json())

    if response.status_code == 200:
        print("Successfully updated deal: {}".format(deal_id))
        return json.loads(response.content)
    else:
        return None


# def delete_deal(deal_id):

#     api_url = '{}deals/{}?api_token={}'.format(api_url_base, deal_id, api_token)

#     response = requests.delete(api_url, headers=headers)
#     # print(response.json())

#     if response.status_code == 200:
#         print("successfully deleted deal: {}".format(deal_id))
#         return json.loads(response.content)
#     else:
#         return None

def get_deal_value(deal_id):

    api_url = '{}deals/{}?api_token={}'.format(api_url_base, deal_id, api_token)

    response = requests.get(api_url, headers=headers)
    # print(response.json())

    if response.status_code == 200:
        existing_value = response.json()["data"]["value"]
        return existing_value
    else:
        return None


def fetch_payload(file_path):

    payload_list = []

    try:
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    payload = {"title": row["title"], "currency": row["currency"], "value": row["value"], "status": row["status"]}
                    payload_list.append(payload)
                    line_count += 1
            return payload_list
            print(f'Processed {line_count} lines.')
    except IOError as e:
        print ("Could not read file:{}".format(e.strerror))
        sys.exit()

async def create_deals_asynchronous(file_path):

    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            payload_list = fetch_payload(file_path)
            create_tasks = [
                loop.run_in_executor(
                    executor,
                    create_deal,
                    *(session, payload)
                )
                for payload in payload_list
            ]
            for id in await asyncio.gather(*create_tasks):
                deal_value = get_deal_value(id)
                transformed_value = float(deal_value) * 2
                transformed_payload = {"value": transformed_value}
                update_tasks = [
                loop.run_in_executor(
                    executor,
                    update_deal,
                    *(session, id, transformed_payload)
                )
            ]
            for response in await asyncio.gather(*update_tasks):
                pass

### Script starts from here ######
if __name__ == '__main__':

    file_path = sys.argv[1] # 'C:\\Users\\rc\\Desktop\\deals.csv'
    api_token = sys.argv[2] # 'a0db207d7780a46a246b8a24f828736b8dcf4435'
    api_url_base = 'https://api.pipedrive.com/v1/'
    headers = {'Accept': 'application/json'}
    transformed_payload_list = []

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(create_deals_asynchronous(file_path))
    loop.run_until_complete(future)