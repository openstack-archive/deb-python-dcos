#!/bin/bash 

apps=(
"rails-app"
"nginx"
)

echo "uninstalling apps"
for app in "${apps[@]}"
do
	dcos marathon destroy $app
done
