#!/usr/bin/env bash

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


function organizeDir()
{
    local dir=$1
    if [ -d dir ]; then
  # Control will enter here if $DIRECTORY exists.
    for i in `find $dir -name '*.mp3'` ; do mkdir -p $dir/music/ && mv i $dir/music/ ;  done
    for i in `find $dir -name '*.flac'` ; mv i $dir/music/ ;  done
    for i in `find $dir -name '*.jpg'` ; do mkdir -p $dir/images/ && mv i $dir/images/ ;  done
    for i in `find $dir -name '*.png'` ; mv i $dir/images/ ;  done
    for i in `find $dir -name '*.avi'` ; do mkdir -p $dir/videos/ && mv i $dir/videos/ ;  done
    for i in `find $dir -name '*.mov'` ; mv i $dir/videos/ ;  done
    for i in `find $dir -name '*.log'` ; do rm -rf i ; done
fi;
}

organizeDir $1

