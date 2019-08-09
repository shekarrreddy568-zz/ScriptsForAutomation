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
#subjects = []
for key in topics_dict:
    if key['num_partitions'] > 50:
        print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
        sys.exit()
    if not key['name'].startswith(nameSpace):
        print("Topic name must start with {}_ , Please fix it and retry!".format(nameSpace))
        sys.exit()
    # if key['value_schema'] == None:
    #     print("Value schema for {} can't be null , Please provide valid subject name".format(key['name']))
    #     sys.exit()
    # subjects.append(key['key_schema'])
    # subjects.append(key['value_schema'])

# subjects_valid = [i for i in subjects if i is not None]
# print ("subjects to be transported:\n {}".format(subjects_valid))

print("Schema Registry URL: " + schema_registry_url)

headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"


def registerSchema():
    for topic in topics_dict:
        subject_names = [topic + "-key" ,topic + "-value" ]
        print ("subject_names: {}".format(subject_names))

        for subject in subject_names:
            ### checking how many versions exist forper subject ###
            get_versions_command = "find {} -regextype egrep -iregex \".*{}-v[0-9]+.*\"  | egrep -i -o \"{}-v[0-9]*\" | sed \"s/{}-v//\" | sort -n".format(schemas_dir,subject,subject,subject)
            versions_to_register = subprocess.check_output(get_versions_command, shell=True, universal_newlines=True).replace("\n",",").split(",")
            valid_versions = [ version for version in versions_to_register if version != '']
            print ("versions_to_register for {}: {}".format(subject,valid_versions))
            for version in valid_versions:
                schema_file = schemas_dir + "/" + subject + "-v" + str(version) + ".avsc"
                print ("schema_file: " + schema_file)
                aboslute_path_to_schema = os.path.join(os.getcwd(), schema_file)
                ### Read schema from file and prepare the post call ###
                with open(aboslute_path_to_schema, 'r') as content_file:
                    schema = content_file.read()

                payload = "{ \"schema\": \"" \
                        + schema.replace("\"", "\\\"").replace("\t", "").replace("\n", "") \
                        + "\" }"

                url = schema_registry + "/subjects/" + subject + "/versions"
                print ("url: " + url)
                ### Registering the schema to the next stage ###
                request = requests.post(url, cert=(cert_path, key_path), headers=headers, data=payload)
                if request.status_code == requests.codes.ok:
                    print("Schema is registered successfully to : {}".format(schema_registry))
                    body = request.content
                    print(body)
                else:
                    result = request.content
                    print ("unable to post schema with the following error, Please fix it and retry!\n{}".format(result))
                    sys.exit()
            #        request.raise_for_status()


registerSchema()
