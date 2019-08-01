import yaml
import requests
import json
import sys
import os
import errno

template = sys.argv[1]
schema_registry = sys.argv[2]
schemas_dir = sys.argv[3]


try: 
    read_template = open(template, "r")
    dictionary = yaml.safe_load(read_template)
except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
    print('Your template file contain invalid YAML syntax! Please fix and retry!\n {}'.format(str(e)))
    sys.exit(1)

### YAML analysis and variable preparation ####
topics_dict = dictionary['topics']
nameSpace = dictionary['nameSpace']
topics = []
topic_partition_map = []
topic_config_map = []
subject_compatability_map = []
headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"

for key in topics_dict:
    if key['num_partitions'] > 50:
        print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
        sys.exit()
    if not key['name'].startswith(nameSpace):
        print("Topic name must start with {}_ , Please fix it and retry!".format(nameSpace))
        sys.exit()
    topic_partition_map.append((key['name'],key['num_partitions']))
    topics.append(key['name'])
    topic_config_map.append((key['name'],key['config']))
#    subject_compatability_map.append((key['subject'][0],key['subject'][1]))

print("topics to be transported:\n {}".format(topics))
topic_partition_dict = dict(topic_partition_map)
topic_config_dict = dict(topic_config_map)
print("topic_partition_map: {}".format(topic_partition_dict))
print("topics configuration is:\n {}".format(topic_config_dict))
#print("subject_compatability_map is: {}".format(subject_compatability_map))

def readSchema(schema_registry,schemas_dir):
    print ("checking if the {} exists if not creating it".format(schemas_dir))
    if not os.path.exists(schemas_dir):
        try:
            os.makedirs(schemas_dir)
            print ("schemas_dir: {} is created".format(schemas_dir))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    else:
        print ("schemas_dir: {} already exists".format(schemas_dir))

    subjects_url = schema_registry + "/subjects"
    subjects = requests.get(subjects_url, cert=(cert_path, key_path))
    if subjects.status_code == requests.codes.ok:
        versions = subjects.json()
        print ("subjects exists in {}: {}".format(schema_registry,subjects))
    else:
        output = subjects.json()
        print ("unable to list subjects from previous stage with the following error, Please fix it and retry!\n{}".format(output))
        sys.exit()

    for topic in topics:
        subject_names = [topic + "-key" ,topic + "-value" ]
        print ("subject_names: {}".format(subject_names))
        for subject in subject_names:
            if subject in subjects:
                ### list the versions for subject ###
                versions_url = schema_registry + "/subjects/" + subject + "/versions"
                r = requests.get(versions_url, cert=(cert_path, key_path))
                if r.status_code == requests.codes.ok:
                    versions = r.json()
                    print ("versions for {}: {}".format(subject,versions))
                else:
                    output = r.json()
                    print ("unable to list schema versions for {} from previous stage with the following error, Please fix it and retry!\n{}".format(subject, output))
                    sys.exit()
                for version in versions:
                    url = schema_registry + "/subjects/" + subject + "/versions/" + str(version)
                    print ("url: " + url)
                    output_file = schemas_dir + "/" + subject + "-v" + str(version) + ".avsc"
                    ### Read perticular version of schema ###
                    request = requests.get(url, cert=(cert_path, key_path))
                    if request.status_code == requests.codes.ok:
                        get_schema = request.json()
                        schema = get_schema['schema']
                        json_load = json.loads(schema)
                        ### Writing the schema to a file ###
                        file = open(output_file, "w")
                        file.write(json.dumps(json_load, indent=4, sort_keys=False))
                        file.close
                        print("schema read is successful and stored in file: {}".format(output_file))
                    else:
                        result = request.json()
                        print ("url: " + url)
                        print ("unable to read schema for {} from previous stage with the following error, Please fix it and retry!\n{}".format(subject, result))
                        sys.exit()
                #        request.raise_for_status()
            else:
                print ("subject {} not found in schema registry: {}".format(subject,schema_registry))

readSchema(schema_registry,schemas_dir)