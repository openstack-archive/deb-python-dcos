#!/bin/bash 

echo "setting up for dcos demo"

echo "removing pre-fetch"
dcos marathon destroy pre-fetch

export PS1="mesosphere> "

