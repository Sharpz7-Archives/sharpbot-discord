#!/bin/bash

# chmod u+x scripts/deploy.sh
# For new install

# Configures and pulls git
git config core.fileMode false
git pull

NAMEOUT="$(uname)"
if [[ $NAMEOUT =~ "MINGW" ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

FILE=.env
if [[ ! -f $FILE ]]; then
    read -p "Please enter your bots key: " -r
    touch $FILE
    echo "SECRET=$REPLY" >> .env
    read -p "Do you want to use Docker? (y/n) " -r
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "NO_DOCKER=TRUE" >> .env
    fi
else
    echo ".env exists..."
fi

# Checks if using docker
source .env
if [[ $NO_DOCKER == "TRUE" ]]; then
    # Non Docker Install
    if [[ -n "$RethinkDB" ]]; then
        echo "Database directory set..."
    else
        NAMEOUT="$(uname)"
        if [[ $NAMEOUT =~ "MINGW" ]]; then
            read -p "Please enter the path for RethinkDB: " -r
            RDB_PATH="$(echo "${REPLY}" | sed 's/\\/\\\\/g')"
            echo "RethinkDB="$RDB_PATH'\\rethinkdb.exe'"" >> .env
        else
            SUDO="sudo"
        fi
            read -p "Please enter the path for RethinkDB: " -r
            echo "RethinkDB={$REPLY}/rethinkdb.exe" >> .env
    fi

    source .env
    start $RethinkDB
    cd project
    pipenv run "py -3.7" -u run.py
else
    # Docker Install
    $SUDO docker system prune -f

    mkdir -p rethink_data
    mkdir -p backups
    SRCDIR="rethink_data"
    DESTDIR="./backups/"
    FILENAME=rethinkdb-$(date +%b-%d-%y).tgz
    tar --create --gzip --file=$DESTDIR$FILENAME $SRCDIR

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

    source .env
    if [[ ! -n "$USE_DOCKERHUB" ]]; then
        read -p "Do you want to pull the latest image? (SIGNIFICANTLY FASTER) (y/n) " -r
        if [[ $REPLY =~ ^[Yy]$ ]];then
            read -p "Please enter your Dockerhub username: " -r
            echo "DOCKERU=$REPLY" >> .env
            read -p "Please enter your Dockerhub password: " -r
            echo "DOCKERP=$REPLY" >> .env
            echo "USE_DOCKERHUB=TRUE" >> .env
        else
            echo "USE_DOCKERHUB=FALSE" >> .env
        fi
    fi

    source .env
    img="sharpbot-discord"
    if [[ -n "$DOCKERU" ]] && [[ "$USE_DOCKERHUB" == "TRUE" ]]; then
        branch="$(git branch | grep \* | cut -d ' ' -f2 |sed 's#/#\-#g')"
        cloud_img="$DOCKERU/$img"

        branch_pull=$(docker pull "$cloud_img:$branch")
        RESULT=$?
        if [[ $RESULT == 0 ]]; then

            echo "Using local branch image..."
            if [[ $branch_pull =~ "Image is up to date" ]]; then
                echo "Image up to date!"
            else
                echo "Tagging local branch to latest."
                docker tag "$cloud_img:$branch" "$img:latest"
            fi

        else
            echo "Using master branch image..."
            branch_pull2=$(docker pull "$cloud_img:master")
            if [[ $branch_pull2 =~ "Image is up to date" ]]; then
                echo "Image up to date!"
            else
                echo "Tagging master branch to latest."
                docker tag "$cloud_img:master" "$img:latest"
            fi
        fi
    else
        echo "Not using dockerhub..."
    fi

    docker build --cache-from "$img:latest" -t "$img:latest" .
    $SUDO docker-compose down
    $SUDO docker-compose up -d
    $SUDO docker-compose logs -f
fi



