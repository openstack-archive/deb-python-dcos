#!/bin/bash 

read -e -p "User ($(whoami)):" user
user=${user:-$(whoami)}
read -e -p "time needed in minutes (default=90): " demo_time
demo_time=${demo_time:-90}
read -e -p "Purpose (client, conference, testing, default=demo): " purpose
purpose=${purpose:-demo}

export TZ=America/Los_Angeles
PST_TIME_START=$(date +"%Z %b %d %H:%M")
PST_TIME_END=$(date -d "+$demo_time minutes" +"%b %d %H:%M")

export TZ=CET
CET_TIME_START=$(date +"%Z %b %d %H:%M")
CET_TIME_END=$(date -d "+$demo_time minutes" +"%b %d %H:%M")


#echo "**** user: $user is using DCOS at $TIME for $demo_time hours ****" | sudo tee /etc/motd
MESSAGE="USER: $user is using DCOS on `hostname -A` for $purpose for $demo_time minutes \nStarting: $PST_TIME_START until $PST_TIME_END\nStarting: $CET_TIME_START until $CET_TIME_END"
echo -e $MESSAGE | sudo tee /etc/motd

echo -e $MESSAGE | wall

echo -e $MESSAGE | /usr/local/bin/slacktee.sh
