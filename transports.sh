#!/usr/bin/env bash

echo
usage() {
  echo "
  Usage: $(basename $0) <EDEN/ERGODEV/ERGO> [ <topic name> <partitions> [ <topic config> ] ]
  Please give environment and if wanted additional params for creating a topic.
  Otherwise all topics in that script will be created if they not exists.

  Example:
  createTopics.sh EDEN kafka.scriptTest 2
  createTopics.sh EDEN kafka.scriptTest 2 \"--config retention.ms=1209600000\"
  createTopics.sh EDEN kafka.scriptTest 2 \"--config retention.ms=1209600000 --config cleanup.policy=compact\"
  "
  exit 1
}

scriptPath="$(dirname $0)/"
source ${scriptPath}vars.sh
source ${scriptPath}helperFunctions.sh
setStage

availableTopics=("openArray" $(kafka-topics --zookeeper ${zooKeeper} --list) "closeArray")
# openArray and closeArray elements in array needed to ensure the check later works probably... bash is not the best for that.

function createTopic()
{
  if [[ ${availableTopics[@]} =~ "${topic}" ]]; then
    echo "Topic already exists, checking for config changes"
    primary_partitions=$(kafka-topics --zookeeper ${zooKeeper} --describe --topic ${topic} | head -n1 | egrep -i -o "PartitionCount:[0-9]*" | sed "s/PartitionCount://")
    if [ ${num_partitions} != ${primary_partitions} ]; then 
      echo "number of partitions differ, hence altering the topic"
      export KAFKA_OPTS="-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf"
      kafka-topics --zookeeper ${zooKeeper} --alter --topic ${topic} --partitions ${num_partitions}
    else
      echo "topic config is same, nothing to change"
    fi;
  else
    echo "Creating new topic"
    export KAFKA_OPTS="-Djava.security.auth.login.config=/etc/kafka/kafka_server_jaas.conf"
    kafka-topics --create --if-not-exists --zookeeper ${zooKeeper} --topic ${topic} --replication-factor ${replication_factor} --partitions ${num_partitions} ${options}
  fi;
}

eval "echo stage name: ${stage}"
eval "echo cluster name: ${cluster}"
eval "echo zookeeper: ${zooKeeper}"
eval "echo total topics: ${total_number_of_topics}"

for i in `seq 1 ${total_number_of_topics}`
do
  eval "topic=\${topic${i}_name}"
  eval "echo topic name: \${topic${i}_name}"
  replication_factor="${defaults_replication_factor}"
  eval "echo replication: \${defaults_replication_factor}"
  eval "num_partitions=\${topic${i}_num_partitions}"
  eval "echo partitions: \${topic${i}_num_partitions}"
  options="${defaults_options_1} ${defaults_options_2}"
  eval "echo options: \${options}"
  createTopic
  i=$(( i++ ))
done


function postValueSchema()
{
sudo python /tmp/transports/scripts/register_schema.py https://${schemaRegistry} ${topic}-value /tmp/transports/schemas/${topic}-value-v${1}.avsc
}

function postKeySchema()
{
sudo python /tmp/transports/scripts/register_schema.py https://${schemaRegistry} ${topic}-key /tmp/transports/schemas/${topic}-key-v${1}.avsc
}

for i in `seq 1 ${total_number_of_topics}`
do
  eval "topic=\${topic${i}_name}"
  num_value_schema_versions=$(find /tmp/transports/schemas -regextype egrep -iregex ".*${topic}-value-v[0-9]+.*"  | egrep -i -o "${topic}-value-v[0-9]*" | sed "s/${topic}-value-v//" | sort -r -n | head -n1)
  num_key_schema_versions=$(find /tmp/transports/schemas -regextype egrep -iregex ".*${topic}-key-v[0-9]+.*"  | egrep -i -o "${topic}-key-v[0-9]*" | sed "s/${topic}-key-v//" | sort -r -n | head -n1)
  echo "num_key_schema_versions=${num_key_schema_versions}"
  echo "num_value_schema_versions=${num_value_schema_versions}"
  eval "key_schema_available=\${topic${i}_key_schema_available}"
  eval "value_schema_available=\${topic${i}_value_schema_available}"
  eval "echo key_schema_available: \${topic${i}_key_schema_available}"
  eval "echo value_schema_available: \${topic${i}_value_schema_available}"
  if ([ ${key_schema_available} = "true" ]); then 
    for j in `seq 1 ${num_key_schema_versions}`
    do
      postKeySchema $j;
    done
  elif ([ ${value_schema_available} = "true" ]); then 
    for j in `seq 1 ${num_value_schema_versions}`
    do
      postValueSchema $j;
    done
  fi;
done
