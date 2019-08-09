#!/usr/bin/env bash

zooKeeper_EDEN_Z="kfkie0z111.linux.eden:2181"
zooKeeper_EDEN_Y="kfkie0y111.linux.eden:2181"
zooKeeper_EDEN_A="kfkie0a111.linux.eden:2181"

bootstrap_EDEN_Z="kfkie0z211.linux.eden:9094"
bootstrap_EDEN_Y="kfkie0z211.linux.eden:9094"
bootstrap_EDEN_A="kfkie0z211.linux.eden:9094"

broker_EDEN_Z="kfkie0z211.linux.eden:9094,kfkie0z222.linux.eden:9094,kfkie0z231.linux.eden:9094,kfkie0z242.linux.eden:9094"
broker_EDEN_Y="kfkie0y211.linux.eden:9094,kfkie0y222.linux.eden:9094,kfkie0y231.linux.eden:9094,kfkie0y242.linux.eden:9094"
broker_EDEN_A="kfkie0a211.linux.eden:9094,kfkie0a222.linux.eden:9094,kfkie0a231.linux.eden:9094,kfkie0a242.linux.eden:9094"

schema_registry_EDEN_Z="kfkie0z313.linux.eden:8081"
schema_registry_EDEN_Y="kfkie0y313.linux.eden:8081"
schema_registry_EDEN_A="kfkie0a313.linux.eden:8081"

readonly red='\033[0;31m'
readonly green='\033[0;32m'
readonly blue='\033[0;34m'
readonly yellow='\033[0;33m'
readonly nc='\033[0m' # No Color
readonly intRegex='^[0-9]+$'

scriptParameters=("openArray" $@ "closeArray")

# Helper functions
LOG() {
  local logLevel="INF"
  local message=""
  local color=

  [[ $# -ge 1 ]] && { message=$1;shift;}
  [[ $# -ge 1 ]] && { logLevel=${message}; message=$1; shift;}

  [[ $logLevel == "INF" ]] && color=${green}
  [[ $logLevel == "ERR" ]] && color=${red}
  [[ $logLevel == "WAR" ]] && color=${yellow}
  [[ $logLevel == "OUT" ]] && color=${nc}
  local additionalMessages="$@"
  local timestamp=`date +\%Y\-%m\-%d\ %H:\%M:\%S`

  echo -e "${color}$timestamp ($$) ##${logLevel}## ${message} ${additionalMessages} ${nc}" 
}

prependLOG() {
  local logMessage=""
  [[ ${1-} ]] && logMessage=$1
  # Adds date and time before output.
  # if used with aws command, you have to specfiy --no-progress there
  while read line; do LOG "OUT" ${logMessage} $line; done
}

setStage() {
    if  ([ ${stage} == "EDEN" ] && [ ${cluster} == "Z" ]); then
        zooKeeper=${zooKeeper_EDEN_Z}
        brokerList=${broker_EDEN_Z}
        bootstrapServer=${bootstrap_EDEN_Z}
        schemaRegistry=${schema_registry_EDEN_Z}
    elif ([ ${stage} == "EDEN" ] && [ ${cluster} == "Y" ]); then
        zooKeeper=${zooKeeper_EDEN_Y}
        brokerList=${broker_EDEN_Y}
        bootstrapServer=${bootstrap_EDEN_Y}
        schemaRegistryURL=${schema_registry_EDEN_Y}
    elif ([ ${stage} == "EDEN" ] && [ ${cluster} == "A" ]); then
        zooKeeper=${zooKeeper_EDEN_A}
        brokerList=${broker_EDEN_A}
        bootstrapServer=${bootstrap_EDEN_A}
        schemaRegistryURL=${schema_registry_EDEN_A}
    else usage;
    fi
}