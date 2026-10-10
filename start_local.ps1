param(
    [switch]$UseDockerServices
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

if (-not (Test-Path .env) -and (Test-Path .env.example)) {
    Copy-Item .env.example .env
}

if ($UseDockerServices) {
    docker compose up -d
}

python manage.py makemigrations api
python manage.py migrate
python manage.py runserver
