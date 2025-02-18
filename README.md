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


## Usage instruction
Setups (one time only)
	!wolfie.set.name aoem_name
		- Tell wolfie your AoEM in game name
	
	!wolfie.set.time timezone_identifier
		- Tell Wolfie your local timezone. Wolfie use your local timezone when display info requested by you.
		- If not set, defaults to UTC.
		- Find yours here: (List of tz database time zones - Wikipedia) use TZ Identifier column for your input

	!wolfie.list - show what Wolfie knows about you

Title request (use as needed)
	!queue.add queue_name [date] [time]
        - Example: !queue.add sage 2-15 3PM		
        - Example: !q sage 3PM
		
	!queue.remove queue_name [date] [time]
		- Example: !queue.remove sage 2-15 3PM
	
	!queue.list queue_name
		- Ex: !queue.list sage
