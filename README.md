# IntegrityBot

## <b>Yet Another Discord music bot that can play songs from Youtube and Soundcloud</b>

### Create bot token:

1. Create a new application on the [Discord Development Portal](https://discord.com/developers/applications).

2. Click on the application you just created, go to "Bot" on the left and click "Add Bot".

3. Scroll down and tick "Presence Intent", "Server Members Intent" and "Message Content Intent".

4. Click on "Reset Token", then save the given token somewhere. Never share it with anyone.

5. Go to "OAuth2" on the left and then "URL Generator". Tick "bot". Then, in the new tab that just opened, give the bot the necessary permissions for your channel (Connect, Speak, Send Messages, Manage Messages). An invite link for the bot should appear below, use it to add the bot to your server.

### Set up bot:

1. Make sure you have Python 3.5 (or above), `pip3` and `ffmpeg` installed on your system. If you don't have them and you're on Windows, you can download Python from [python.org](https://www.python.org/) and you can install `ffmpeg` by following [this tutorial](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/). If you're on Linux, use your distro's package manager.

2. Download the files from this repo (either `git clone` through your terminal, or download and extract the zip from Github).

3. Install requirements with pip.

4. Open the `config.ini` file and insert the token that you were given in step 4 of "Create bot token", then save.

5. Make additional modifications to the `config.ini`as appropriate. If the file doesn't exist, run the program to create it.

6. Run the `main.py` file using Python3.

### YouTube restrictions

1. You can authenticate to allow you to watch age-restricted videos and others that require a login. If this is not something you want, you can disable it in the config.

2. When a video is queued, you will be promted with a code in the console. Go to google.com/device and enter the code, select a YouTube account (not a google account, even if it's your primary YouTube!), then press Enter in the console.

### Credits:

Readme and code adapted from MuseBot
https://github.com/cyber-sushi/musebot
