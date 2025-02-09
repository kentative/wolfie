#!/bin/bash

source wolfie/bin/activate
nohup python bot.py > output.log 2>&1 &
echo $! > wolfie.pid
