function build_image {
    docker build --rm -f "Dockerfile" -t sharpbot-discord:latest .
}

function backup {
    $source = "rethink_data"
    $dest = "./backups/"
    $date = Get-Date -Format MMM-dd-yy
    $filename = "rethinkdb-$date.tgz"
    tar --create --gzip --file=$dest$filename $source
}

try {
    docker-compose down
}
catch {
    "docker and docker-compose must be installed for deployment. exiting..."
    exit
}

git config core.fileMode false

mkdir -p rethink_data -Force > $null
mkdir -p backups -Force > $null
backup

$gitlog = git pull
$file = "Dockerfile"
if ($gitlog -like $file ) {
    build_image
    "backup completed..."
}
else {
    "no changes to dockerfile..."
}

if (!(Test-Path ".env")) {
    $key = Read-Host -Prompt "please enter your bots key: "
    New-Item -name .env -type "file" -value "SECRET=$key"
    "created env file..."
}
else {
    ".env exists..."
}

"booting..."

docker system prune -f
docker-compose up -d
docker-compose logs -f
