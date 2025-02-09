## Raspberry pi setup

### Installation for bookworm
1. `git clone https://github.com/kentative/wolfie.git && cd wolfie` 
2. `python -m venev wolfie`
3. `source wolfie/bin/activate`
4. `pip3 install -r requirements.txt`

### Start wolfie (start.py or these steps)
1. Define required values in .env file
2. `source wolfie/bin/activate`
3. `nohup python bot.py > output.log 2>&1 &`
4. `echo $! > wolfie.pid`

### Stop wolfie
1. `kill $(cat wolfie.pid)`