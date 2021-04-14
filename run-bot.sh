#!/bin/sh
pgrep python
if [ $? = 1 ]
then
cd /home/kilian/BOTS/dogsbot/
/home/kilian/.pyenv/versions/dogsbot/bin/python /home/kilian/BOTS/dogsbot/main.py&
fi
