#!/bin/sh
pgrep -f "/usr/bin/SCREEN -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py"

if [ $? -eq 1 ]
then
cd /home/kilian/bots/dogsbot/
/usr/bin/screen -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py
fi
