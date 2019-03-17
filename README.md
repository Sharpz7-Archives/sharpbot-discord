[![CircleCI](https://circleci.com/gh/Sharpz7/sharpbot-discord.svg?style=svg)](https://circleci.com/gh/Sharpz7/sharpbot-discord)
[![Discord](https://img.shields.io/discord/467653644179996683.svg?style=popout)](https://discord.gg/JvQTwVW)


Sharpbot: Discord bot for Python 3.
============================================
**Make sure you have made a bot account!**

Required
============
Docker and Docker-compose are needed for docker installations.

Pipenv and Python 3.7 are needed for non-docker installs.

Installation (Unix - Shellscript)
============

Clone or download the repository.

> \$ git clone https://gitlab.com/Sharpz7/sharpbot-discord.git
> \$ cd sharpbot-discord

Make sure the script is executable.

> \$ chmod u+x scripts/deploy.sh

Now that it is executable, run the bash script that it should install!

> \$ scripts/deploy.sh

Installation (Windows - Poweshell)
============

Clone or download the repository.

> \$ git clone https://gitlab.com/Sharpz7/sharpbot-discord.git
> \$ cd sharpbot-discord

Run the .ps1 powershell script

> \$ scripts/deploy.ps1

Installation (Without Docker - Python 3.7.2 Tested)
============

Clone or download the repository.

> \$ git clone https://gitlab.com/Sharpz7/sharpbot-discord.git
> \$ cd sharpbot-discord

Install all the requirements using pipenv.

> \$ pipenv install

Create a .env file and put your key inside this file.

> \$ touch .env
```
SECRET=<YOUR-KEY>
NO_DOCKER=TRUE
```

Run the code from the included script and follow instructions

> \$ scripts/non-docker.bat

**Non docker installs require python 3.7!!**

Maintainers and Developers
==========

-   Sharp / [@Sharpz7](https://github.com/Sharpz7)

-   Kingsley McDonald / [@kingdom5500](https://github.com/kingdom5500)

-   issuemeaname / [@issuemeaname](https://github.com/issuemeaname)

