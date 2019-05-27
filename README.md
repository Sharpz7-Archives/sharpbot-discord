[![CircleCI](https://circleci.com/gh/Sharpz7/sharpbot-discord.svg?style=svg)](https://circleci.com/gh/Sharpz7/sharpbot-discord)
[![Discord](https://img.shields.io/discord/467653644179996683.svg?style=popout)](https://discord.gg/JvQTwVW)
[![Python](https://img.shields.io/badge/python-3.7+-yellow.svg)](https://www.python.org/downloads/release/python-370/)
[![Rethink](https://img.shields.io/badge/rethink-recent-blue.svg)](https://rethinkdb.com/docs/install/windows/)


Sharpbot: Discord bot for Python 3.
============================================
**Make sure you have made a discord bot account!**

Required
============
Docker and Docker-compose are needed for docker installations.

Pipenv and Python 3.7 are needed for non-docker installs.

RethinkDB needs to be installed for non-docker installs.

Installation
============

If you want to use the scipts provided, this is the easiest way to install the bot.

This will work for docker and non-docker installs.

Clone or download the repository.

> \$ git clone https://github.com/Sharpz7/sharpbot-discord.git
> \$ cd sharpbot-discord

For unix, make sure the script is executable.

> \$ chmod u+x scripts/deploy.sh

Now that it is executable, run the bash or powershell script and it should install!

> \$ scripts/deploy.sh
> \$ scripts/deploy.ps1

You can use these scripts everytime you want to run the bot - It will automatically keep it updated!

Installation (Without Scripts)
============

This is a example without docker.
If you want to use docker, its highly recommended you use the scripts.

Clone or download the repository.

> \$ git clone https://github.com/Sharpz7/sharpbot-discord.git
> \$ cd sharpbot-discord

Install all the requirements using pipenv.

> \$ pipenv install

Create a .env file and put your key inside this file.

> \$ touch .env
```
SECRET=<YOUR-KEY>
NO_DOCKER=TRUE
```

Download and install a recent [RethinkDB](https://rethinkdb.com/docs/install/windows/) package and run.
Now run the code by doing:

> \$ pipenv run python run.py

**Non docker installs require python 3.7!!**

Maintainers and Developers
==========

-   Sharp / [@Sharpz7](https://github.com/Sharpz7)

-   Kingsley McDonald / [@kingdom5500](https://github.com/kingdom5500)

-   issuemeaname / [@issuemeaname](https://github.com/issuemeaname)

All Supported Env Vars
========================

```go
// Required
SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
RESTART=no

// Not Required
NO_DOCKER=FALSE
USE_DOCKERHUB=TRUE
RethinkDB=location/of/rethink/install
DEVMODE=TRUE
CICD=TRUE
DOCKERU=<docker_username>
DOCKERP=<docker_password>
SKIPBUILD=TRUE
```

