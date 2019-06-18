import os
import sys
import yaml
import requests

template = sys.argv[1]
schema_registry_url = sys.argv[2]
schemas_dir = sys.argv[3]

try:
    read_template = open(template, "r")
    dictionary = yaml.safe_load(read_template)
except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
    print('Your template file contain invalid YAML syntax! Please fix and retry!\n {}'.format(str(e)))
    sys.exit()

topics_dict = dictionary['topics']
nameSpace = dictionary['nameSpace']
subjects = []
for key in topics_dict:
    if key['num_partitions'] > 50:
        print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
        sys.exit()
    if not key['name'].startswith(nameSpace):
        print("Topic name must start with {}_ , Please fix it and retry!".format(nameSpace))
        sys.exit()
    if key['value_schema'] == None:
        print("Value schema for {} can't be null , Please provide valid subject name".format(key['name']))
        sys.exit()
    subjects.append(key['key_schema'])
    subjects.append(key['value_schema'])

subjects_valid = [i for i in subjects if i is not None]
print ("subjects to be transported:\n {}".format(subjects_valid))

print("Schema Registry URL: " + schema_registry_url)

headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
#cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
#key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"


def registerSchema(subject):
    schema_file = schemas_dir + subject + ".avsc"
    aboslute_path_to_schema = os.path.join(os.getcwd(), schema_file)
    
    with open(aboslute_path_to_schema, 'r') as content_file:
        schema = content_file.read()

    payload = "{ \"schema\": \"" \
            + schema.replace("\"", "\\\"").replace("\t", "").replace("\n", "") \
            + "\" }"

    url = schema_registry_url + "/subjects/" + subject + "/versions"
    request = requests.post(url, headers=headers, data=payload)
#    request = requests.post(url, cert=(cert_path, key_path), headers=headers, data=payload)
    if request.status_code == requests.codes.ok:
        print("Schema is registered successfully to url: {}".format(schema_registry_url))
        body = request.json()
        print(body)
    else:
        result = request.json()
        print ("unable to post schema with the following error, Please fix it and retry!\n{}".format(result))
        sys.exit()
#        request.raise_for_status()

for i in subjects_valid:
    registerSchema(i)
