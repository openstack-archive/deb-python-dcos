#!/bin/bash 

apps=(
"rails-app"
"nginx"
)

echo "Uninstalling apps..."
for app in "${apps[@]}"
do
	echo "uninstalling app: $app"
	{
	  dcos marathon destroy $app
	} &> /dev/null
done
echo "Demo Apps Uninstalled!"
