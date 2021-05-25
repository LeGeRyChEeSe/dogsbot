#!/bin/sh

dogsbot=$(pgrep -f "SCREEN -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py")

if [ $? -eq 0 ]
then
sudo kill $dogsbot
fi

cd /home/kilian/bots/dogsbot/
sudo screen -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py
