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

$d = source
if ($d["NO_DOCKER"] -eq "TRUE") {
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
}
