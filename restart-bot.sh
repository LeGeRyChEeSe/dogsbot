#!/bin/sh

dogsbot=$(pgrep -f "SCREEN -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py")
sudo kill $dogsbot
sudo screen -dmS dogsbot /home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/bots/dogsbot/main.py
