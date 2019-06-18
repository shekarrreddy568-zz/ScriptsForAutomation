import yaml
import requests
import json
import sys
import os
import errno
import subprocess

template = sys.argv[1]
### checking the YAML syntax ###
try: 
    read_template = open(template, "r")
    dictionary = yaml.safe_load(read_template)
except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
    print('Your template file contain invalid YAML syntax! Please fix and retry!\n {}'.format(str(e)))
    sys.exit()

### YAML analysis and variable preparation ####
topics_dict = dictionary['topics']
nameSpace = dictionary['nameSpace']
topics = []
map_topics = []
for key in topics_dict:
    if key['num_partitions'] > 50:
        print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
        sys.exit()
    if not key['name'].startswith(nameSpace):
        print("Topic name must start with {}_ , Please fix it and retry!".format(nameSpace))
        sys.exit()
    map_topics.append((key['name'],key['num_partitions']))
    topics.append(key['name'])

print ("topics to be transported:\n {}".format(topics))
topic_partition_map = dict(map_topics)
print ("topic_partition_map: {}".format(topic_partition_map))

### Variables ddefinition ###
headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"

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

def registerSchema(schema_registry,schemas_dir):
    for topic in topics:
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

def createTopic(zookeeper):
    ### Listing the existing topics ###
    get_topics = subprocess.check_output(["kafka-topics --zookeeper {}:2181 --list".format(zookeeper)], shell=True, universal_newlines=True) 
    existing_topics = list(get_topics.split("\n"))
    
    for topic in topics:
        ### checking the desired partitions from yaml template ###
        desired_partitions = topic_partition_map['{}'.format(topic)]
        print ("desired_partitions: {}".format(desired_partitions))
        if topic in existing_topics:
            print ("Topic already exists, checking for config changes")
            command = "export KAFKA_OPTS=\"-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf\"; kafka-topics --zookeeper {}:2181 --describe --topic {} | head -n1 | egrep -i -o \"PartitionCount:[0-9]*\" | sed \"s/PartitionCount://\"".format(zookeeper,topic)
            ### getting the existing partitions from topic ###
            get_primary_partitions = subprocess.check_output(command,shell=True,universal_newlines=False).replace("\n","")
            primary_partitions = int(get_primary_partitions)
            print ("primary_partitions: {}".format(primary_partitions))

            if desired_partitions != primary_partitions:
                print ("Altering the topic partitions")
                cmd = "export KAFKA_OPTS=\"-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf\"; kafka-topics --zookeeper {}:2181 --alter --topic {} --partitions {}".format(zookeeper,topic,desired_partitions)
                result = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                print (result)
            else:
                print ("topic config is same, nothing to change")

        else:
            print ("Creating new topic")
            subprocess.call(["export KAFKA_OPTS=\"-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf\""], shell=True, universal_newlines=True)
            result = subprocess.check_output(["export KAFKA_OPTS=\"-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf\"; kafka-topics --create --if-not-exists --zookeeper {}:2181 --topic {} --replication-factor 3 --partitions {}".format(zookeeper,topic,desired_partitions)], shell=True, universal_newlines=True)
            print (result)