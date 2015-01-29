#!/bin/bash 

services=(
"spark"
"cassandra"
"kafka"
"chronos"
"jenkins"
"hdfs"
"deis"
"hadoop"
"yarn"
"accumulo"
"elasticsearch"
"aurora"
"storm"
"chaos"
)

echo "uninstalling services"
for service in "${services[@]}"
do
	dcos uninstall $service
done
