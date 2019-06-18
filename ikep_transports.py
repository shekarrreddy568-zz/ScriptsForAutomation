#!/usr/bin/env python
#
# Copyright 2019 - IKEP
# The script is for transporting the IKEP topic configuration and schemas to the next stages
# You can find the file in itergo github repo 

import yaml
import requests
import json
import sys
import os
import errno
import subprocess
from confluent_kafka.admin import AdminClient, NewTopic, NewPartitions, ConfigResource, ConfigSource
from confluent_kafka import KafkaException
import threading
import logging

### Function Definitions #####

def registerSchema(schema_registry):
    for list in subjects_list:
        for dict in list:
            subject_name = dict['name']
            if subject_name != None:
                print("subject_name is {}".format(subject_name))
                mode = dict['subjectCompatibility']
                print("mode is {}".format(mode))
                schema_versions = dict['versions']
                for version in schema_versions:
                    payload = "{\"schema\": \"" \
                        + version['schema'].replace("\"", "\\\"") \
                        + "\"}"
                    #print("payload is {}".format(payload))

                    url = schema_registry + "/subjects/" + subject_name + "/versions"
                    print ("url: " + url)
                    ### Registering the schema to the next stage ###
                    #request = requests.post(url, cert=(cert_path, key_path), headers=headers, data=payload)
                    request = requests.post(url, headers=headers, data=payload)
                    if request.status_code == requests.codes.ok:
                        print("Schema is registered successfully to : {}".format(schema_registry))
                        body = request.content
                        print(body)
                    else:
                        result = request.content
                        print ("unable to post schema with the following error, Please fix it and retry!\n{}".format(result))
                        sys.exit()
                #        request.raise_for_status()

def list_topics(a):
    existing_topics = []
    existing_partitons = []
    md = a.list_topics(timeout=10)

    for t in iter(md.topics.values()):
        existing_topics.append(str(t))
        existing_partitons.append((str(t),len(t.partitions)))

    print("existing_topics are: {}".format(existing_topics))
    existing_partiton_map = dict(existing_partitons)
    print("existing_partiton_map are: {}".format(existing_partiton_map))

def create_topic(a, topic, partitions, replication_factor):
    """ Create topics """
    new_topic = [NewTopic(topic, partitions, replication_factor)]
    # Call create_topics to asynchronously create topics, a dict of <topic,future> is returned.
    fs = a.create_topics(new_topic)

    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))

def delete_topic(a, topic_name):
    """ delete topics """
    topics = [topic_name]
    fs = a.delete_topics(topics, operation_timeout=30)

    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))

def alter_partitions(a, topic, partitions):
    """ create partitions """

    new_parts = [NewPartitions(topic, partitions)]

    # Try switching validate_only to True to only validate the operation
    # on the broker but not actually perform it.
    fs = a.create_partitions(new_parts, validate_only=False)

    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Additional partitions created for topic {}".format(topic))
        except Exception as e:
            print("Failed to add partitions to topic {}: {}".format(topic, e))

def describe_configs(a, topic):
    """ describe configs """

    resources = [ConfigResource("TOPIC",topic)]
    fs = a.describe_configs(resources)

    # Wait for operation to finish.
    for res, f in fs.items():
        try:
            configs = f.result()
            config_list = []
            for config in iter(configs.values()):
                config_list.append(tuple(str(config).split("=")))
                config_dict = dict(config_list)
            print(config_dict)
            
        except KafkaException as e:
            print("Failed to describe {}: {}".format(res, e))
        except Exception:
            raise

def alter_configs(a, topic):
    """ Alter configs atomically, replacing non-specified
    configuration properties with their default values.
    """
    resources = []
    resource = ConfigResource("TOPIC", topic)
    resources.append(resource)
    for x in topic_config_dict['{}'.format(topic)]:
        key = x
        #print("key: {}".format(key))
        value = topic_config_dict['{}'.format(topic)]['{}'.format(x)]
        #print("value: {}".format(value))
        resource.set_config(key, value)

    fs = a.alter_configs(resources)

    # Wait for operation to finish.
    for res, f in fs.items():
        try:
            f.result()  # empty, but raises exception on failure
            print("topic {} configuration successfully altered".format(res.name))
        except Exception:
            raise

def compatability_check(schema_registry):
    for list in subjects_list:
        for dict in list:
            subject_name = dict['name']
            if subject_name != None:
                mode = dict['subjectCompatibility']
                print("desired compatability mode for {} is: {}".format(subject_name,mode))
                if mode != None:
                    if mode != "BACKWARD":
                        payload = "{\"compatibility\":\"%s\"}" % mode
                        url = schema_registry + "/config/"
                        #r = requests.put(url, data=payload, headers=headers, cert=(cert_path, key_path))
                        r = requests.put(url, headers=headers, data=payload)
                        if r.status_code == requests.codes.ok:
                            result = r.json()
                            print ("compatibility mode changed to: {}".format(result))
                        else:
                            output = r.json()
                            print ("unable to change the compatability mode for {} with the below error\n {}".format(subject_name,output))
                            sys.exit()
                    else:
                        print("compatibility is the default one: {}".format(mode))


def adminClientAPI(a):

    """list topics"""
    existing_topics = []
    existing_partitons = []
    md = a.list_topics(timeout=10)

    for t in iter(md.topics.values()):
        existing_topics.append(str(t))
        existing_partitons.append((str(t),len(t.partitions)))

    print("existing_topics are: {}".format(existing_topics))
    existing_partiton_map = dict(existing_partitons)
    print("existing_partiton_map are: {}".format(existing_partiton_map))

    for topic in topics:
        desired_partitions = topic_partition_dict['{}'.format(topic)]
        replication_factor = 1
        if topic not in existing_topics:
            create_topic(a, topic, desired_partitions, replication_factor)
        else:
            print("topic {} already exists, checkin for partition changes".format(topic))
            existing_partitions = existing_partiton_map['{}'.format(topic)]
            if (desired_partitions != existing_partitions):
                print("alterting the partitions for {} from {} to {}".format(topic,existing_partitions,desired_partitions))
                alter_partitions(a, topic, desired_partitions)
            else:
                print("num_partitions are same for {}".format(topic))
        
        print("applying or changing the topic configuration")
        alter_configs(a, topic)
        print("describing the configuration")
        describe_configs(a, topic)


### Script starts from here ######
if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.stderr.write('Usage: %s <template> <schema_registry> <bootstrap_servers> <schemas_dir>\n' % sys.argv[0])
        sys.stderr.write('Please pass all the required parameters')
        sys.exit(1)

    template = sys.argv[1]
    schema_registry = sys.argv[2]
    bootstrap_servers = sys.argv[3]

    ### checking the YAML syntax ###
    try: 
        read_template = open(template, "r")
        dictionary = yaml.safe_load(read_template)
    except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
        print('Your template file contain invalid YAML syntax! Please fix and retry!\n {}'.format(str(e)))
        sys.exit(1)

    ### YAML analysis and variable preparation ####
    topics_dict = dictionary['topics']
    namespace = dictionary['namespace']
    topics = []
    topic_partition_map = []
    topic_config_map = []
    subjects_list = []
    headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
    cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
    key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"
    security_protocol = "SSL"
    ssl_ca_location = "/mnt/cifsConfluentPlatform/ssl_certs/certs_CA_eden/ERGO_ROOT_CA_eden.cer"
    ssl_cert_location = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_C1/client.ITERGO_C1.cer.pem"
    ssl_key_location = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_C1/client.ITERGO_C1.keystore.key"

    for key in topics_dict:
        if key['partitions'] > 50:
            print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
            sys.exit()
        if not key['name'].startswith(namespace):
            print("Topic name must start with {}_ , Please fix it and retry!".format(namespace))
            sys.exit()
        topic_partition_map.append((key['name'],key['partitions']))
        topics.append(key['name'])
        topic_config_map.append((key['name'],key['configs']))
        subjects_list.append(key['subjects'])

    print("topics to be transported:\n {}".format(topics))
    topic_partition_dict = dict(topic_partition_map)
    topic_config_dict = dict(topic_config_map)
    print("topic_partition_map: {}".format(topic_partition_dict))
    #print("topics configuration is:\n {}".format(topic_config_dict))
    #print("subjects_list is: {}".format(subjects_list))


    ### Create AdminClient ###
    a = AdminClient({'bootstrap.servers': bootstrap_servers}) 
    # a = AdminClient({
    # 'bootstrap.servers': bootstrap_servers,
    # 'security.protocol': security_protocol,
    # 'ssl.ca.location': ssl_ca_location,
    # 'ssl.certificate.location': ssl_cert_location,
    # 'ssl.key.location': ssl_key_location
    # })

    ### functions ###
    registerSchema(schema_registry)
    #compatability_check(schema_registry)
    adminClientAPI(a)