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

echo "Uninstalling services..."
for service in "${services[@]}"
do
	echo "uninstalling service: $service"
	{
	  dcos uninstall $service
	} &> /dev/null
done
echo "Demo services Uninstalled!"
