#!/bin/bash

# chmod u+x deploy.sh
# For new install

build_image () {
    $SUDO docker build --rm -f "Dockerfile" -t sharpbot-discord:latest .
}

backup () {
    SRCDIR="rethink_data"
    DESTDIR="./backups/"
    FILENAME=rethinkdb-$(date +%b-%d-%y).tgz
    tar --create --gzip --file=$DESTDIR$FILENAME $SRCDIR
}

NAMEOUT="$(uname)"
if [[ $NAMEOUT =~ "MINGW" ]]; then
    SUDO=""
else
    SUDO="sudo"
fi


git config core.fileMode false
$SUDO docker system prune -f
mkdir -p rethink_data
mkdir -p backups
backup

docker_version="$($SUDO docker version)"
RESULT=$?
if [[ $RESULT != 0 ]]; then
    echo "docker must be installed for deployment. Exiting..."
    exit
else
    echo "Found docker"
fi

docker_version="$($SUDO docker-compose version)"
RESULT=$?
if [[ $RESULT != 0 ]]; then
    echo "docker-compose must be installed for deployment. Exiting..."
else
    echo "Found docker-compose"
fi

GITLOG= git pull
FILE="Dockerfile"
if [[ $GITLOG =~ $FILE ]];
then
    build_image
else
    echo "No changes to dockerfile"
fi

FILE=.env
if [[ ! -f $FILE ]]; then
    read -p "Please enter your bots key: " -r
    touch .env
    echo "SECRET=$REPLY" > .env
else
    echo ".env exists..."
fi

$SUDO docker-compose down
$SUDO docker-compose up -d
$SUDO docker-compose logs -f
