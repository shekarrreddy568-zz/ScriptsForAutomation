import yaml
import json
import sys
import os
import errno
from confluent_kafka.admin import AdminClient, NewTopic, NewPartitions, ConfigResource, ConfigSource
from confluent_kafka import KafkaException
import threading
import logging

logging.basicConfig()

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
config_map = []
for key in topics_dict:
    if key['num_partitions'] > 50:
        print("number of partitions for {} can't be greater than 50 (ikep restriction)".format(key['name']))
        sys.exit()
    if not key['name'].startswith(nameSpace):
        print("Topic name must start with {}_ , Please fix it and retry!".format(nameSpace))
        sys.exit()
    map_topics.append((key['name'],key['num_partitions']))
    topics.append(key['name'])
    config_map.append((key['name'],key['config']))


print ("topics to be transported:\n {}".format(topics))
topic_partition_map = dict(map_topics)
topic_config_map = dict(config_map)
print ("topics configuration is:\n {}".format(topic_config_map))
print ("topic_partition_map: {}".format(topic_partition_map))

### Variables ddefinition ###
headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
cert_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.cer"
key_path = "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_ANSIBLE/client.ITERGO_ANSIBLE.keystore.key"


# Create Admin client
#a = AdminClient({'bootstrap.servers': broker})
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
    for x in topic_config_map['{}'.format(topic)]:
        key = x
        print("key: {}".format(key))
        value = topic_config_map['{}'.format(topic)]['{}'.format(x)]
        print("value: {}".format(value))
        resource.set_config(key, value)

    fs = a.alter_configs(resources)

    # Wait for operation to finish.
    for res, f in fs.items():
        try:
            f.result()  # empty, but raises exception on failure
            print("{} configuration successfully altered".format(res))
        except Exception:
            raise

def adminClientAPI(broker):
    a = AdminClient({'bootstrap.servers': broker}) 
    # a = AdminClient({'bootstrap.servers': broker,
    # 'security.protocol': "SSL",
    # 'ssl.ca.location': "/mnt/cifsConfluentPlatform/ssl_certs/certs_CA_eden/ERGO_ROOT_CA_eden.cer",
    # 'ssl.certificate.location': "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_C1/client.ITERGO_C1.cer.pem",
    # 'ssl.key.location': "/mnt/cifsConfluentPlatform/ssl_certs/clients/ITERGO_C1/client.ITERGO_C1.keystore.key",
    # 'ssl.key.password': "CLIENT" })

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
        desired_partitions = topic_partition_map['{}'.format(topic)]
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
        delete_topic(a, topic)