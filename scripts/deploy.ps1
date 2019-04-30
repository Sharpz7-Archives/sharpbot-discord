function source {
    $d = @{}
    $array = Get-Content .\.env
    foreach ($item in $array) {
        $name, $value = $item.split("=")
        $d[$name] = $value
    }
    return $d
}

function gitbranch {
    $data = git branch
    foreach ($line in $data) {
        if ($line.Contains('*')) {
            $b = $line.substring(2)
            $final = $b.replace("/", "-")
            return $final
        }
    }
}

git config core.fileMode false
git pull

if (!(Test-Path ".env")) {
    $key = Read-Host -Prompt "Please enter your bots key"
    (New-Item -name .env) > $null
    "SECRET=$key"| Out-File .env -Append -Encoding OEM
    $key = Read-Host -Prompt "Do you want to use Docker? (y/n) "
    if ($key -like "n") {
        "NO_DOCKER=TRUE"| Out-File .env -Append -Encoding OEM
    }
}
else {
    ".env exists..."
}

$d = source
if ($d["NO_DOCKER"] -eq "TRUE") {
    if ($d.ContainsKey("RethinkDB")) {
        "Database directory set..."
    }
    else {
        $key = Read-Host -Prompt "Please enter the path for RethinkDB"
        $db = $key.replace("\", "\\") + "\\rethinkdb.exe"
        "RethinkDB=$db"| Out-File .env -Append -Encoding OEM
    }

    $d = source
    start $d["RethinkDB"]
    cd project
    pipenv run "py -3.7" -u run.py
}
else {
    docker-compose down
    $result = $?
    if ($result) {
        "Found docker..."
    }
    else {
        "Docker and docker-compose must be running/installed for deployment. exiting..."
        exit 1
    }

    docker system prune -f

    mkdir -p rethinkdb_data -Force > $null
    mkdir -p backups -Force > $null
    $source = "rethinkdb_data"
    $dest = "./backups/"
    $date = Get-Date -Format MMM-dd-yy
    $filename = "rethinkdb-$date.tgz"
    tar --create --gzip --file=$dest$filename $source

    $d = source
    if (!($d.ContainsKey("USE_DOCKERHUB"))) {
        $key = Read-Host -Prompt "Do you want to pull the latest image? (SIGNIFICANTLY FASTER) (y/n)"
        if ($key -like "y") {
            $key = Read-Host -Prompt "Please enter your Dockerhub username"
            "DOCKERU=$key"| Out-File .env -Append -Encoding OEM
            $key = Read-Host -Prompt "Please enter your Dockerhub password"
            "DOCKERP=$key"| Out-File .env -Append -Encoding OEM
            "USE_DOCKERHUB=TRUE"| Out-File .env -Append -Encoding OEM
        }
        else {
            "USE_DOCKERHUB=FALSE"| Out-File .env -Append -Encoding OEM
        }
    }

    $d = source
    $img = "sharpbot-discord"
    if (($d.ContainsKey("DOCKERU")) -and ($d["USE_DOCKERHUB"] -eq "TRUE")) {
        $branch = gitbranch
        $user = $d['DOCKERU']
        $cloud_img = "$user/$img"

        $branch_pull = docker pull "${cloud_img}:$branch"
        $result = $?
        if ($result) {
            "Using local branch image..."
            if ( $branch_pull -Match "Image is up to date") {
                "Image up to date!"
            }
            else {
                "Tagging local branch to latest."
                docker tag "${cloud_img}:$branch" "${img}:latest"
            }
        }
        else {
            docker pull "${cloud_img}:master" > $branch_pull2 | out-null
            "Using master branch image..."
            if ( $branch_pull2 -Match "Image is up to date") {
                "Image up to date!"
            }
            else {
                "Tagging master branch to latest."
                docker tag "${cloud_img}:master" "${img}:latest"
            }
        }
    }
    else {
        "Not using dockerhub..."
    }

    if ($d["SKIPBUILD"] -eq "TRUE") {
        "Skipping build..."
    }
    else {
        docker build --cache-from "${img}:latest" -t "${img}:latest" .
    }

    docker-compose up -d
    docker-compose logs -f
}
