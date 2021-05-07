#!/bin/sh
pgrep -f "SCREEN -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/BOTS/dogsbot/main.py"

if [ $? -eq 1 ]
then
cd /home/kilian/BOTS/dogsbot/
screen -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/BOTS/dogsbot/main.py
fi
