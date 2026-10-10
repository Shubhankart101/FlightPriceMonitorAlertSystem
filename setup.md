# PulseNotify Setup Guide

This guide contains command-ready steps to run PulseNotify locally and deploy it to cloud infrastructure.

## 1. Prerequisites

## 1.1 Required tools

- Git
- Python 3.10+
- Docker Desktop
- Terraform 1.6+
- Azure CLI
- GitHub CLI (optional, for workflow operations)

## 1.2 Clone repository

Windows PowerShell:
```powershell
git clone git@github.com:Shubhankart101/FlightPriceMonitorAlertSystem.git
cd FlightPriceMonitor-AlertSystem
```

Linux/macOS:
```bash
git clone git@github.com:Shubhankart101/FlightPriceMonitorAlertSystem.git
cd FlightPriceMonitor-AlertSystem
```

## 2. Local setup and run

## 2.1 Environment variables

Create local environment file from template.

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

Linux/macOS:
```bash
cp .env.example .env
```

Default local mode uses SQLite (`DB_ENGINE=sqlite`) so local run works without PostgreSQL.

## 2.2 Option A: Quick start script (Windows)

```powershell
.\start_local.ps1
```

With Docker-backed Redis/PostgreSQL:
```powershell
.\start_local.ps1 -UseDockerServices
```

## 2.3 Option B: Manual setup

Windows PowerShell:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations api
python manage.py migrate
python manage.py runserver
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations api
python manage.py migrate
python manage.py runserver
```

## 2.4 Run background workers

Start each command in a dedicated terminal after venv activation.

Windows PowerShell:
```powershell
celery -A pulse worker -l info
celery -A pulse beat -l info
```

Linux/macOS:
```bash
celery -A pulse worker -l info
celery -A pulse beat -l info
```

## 2.5 Local verification endpoints

- Health: `http://127.0.0.1:8000/api/health/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## 3. Container build and run

## 3.1 Build image

Windows PowerShell and Linux/macOS:
```bash
docker build -t pulsenotify:local .
```

## 3.2 Run container

Windows PowerShell and Linux/macOS:
```bash
docker run --rm -p 8000:8000 --env-file .env pulsenotify:local
```

## 4. GitHub pipelines

Workflows are in `.github/workflows/`.

- `validate.yml`: validation checks for app and Terraform
- `test.yml`: dedicated test pipeline
- `build-deploy.yml`: image build and Azure web app deploy
- `infra-terraform.yml`: Terraform plan/apply

## 4.1 Trigger workflows from CLI (optional)

```bash
gh workflow run "Validation Pipeline"
gh workflow run "Test Pipeline"
gh workflow run "Build and Deploy Pipeline"
gh workflow run "Terraform IaC Pipeline"
```

## 5. Azure cloud deployment

## 5.1 Authenticate Azure

Windows PowerShell and Linux/macOS:
```bash
az login
az account set --subscription "<your-subscription-id>"
```

## 5.2 Configure Terraform variables

Windows PowerShell:
```powershell
cd infra/terraform/environments/dev
Copy-Item terraform.tfvars.example terraform.tfvars
```

Linux/macOS:
```bash
cd infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Update `terraform.tfvars` values:

- `docker_image_name`
- `django_secret_key`
- `db_admin_password`

## 5.3 Deploy infrastructure with Terraform

Windows PowerShell and Linux/macOS:
```bash
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## 5.4 Configure GitHub secrets for deploy pipelines

Set these repository secrets in GitHub:

- `AZURE_CREDENTIALS`
- `AZURE_WEBAPP_NAME`
- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`
- `ARM_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## 5.5 Push and deploy via pipeline

```bash
git add -A
git commit -m "Deploy-ready changes"
git push origin main
```

Build/deploy workflow publishes image to GHCR and deploys app to Azure Web App when required secrets exist.

## 6. Useful commands

## 6.1 Git pull and push over SSH

```bash
git remote -v
git pull --rebase --autostash origin main
git push origin main
```

## 6.2 Django admin and tests

```bash
python manage.py createsuperuser
python manage.py check
python manage.py test -v 2
```

## 6.3 Terraform teardown

From `infra/terraform/environments/dev`:
```bash
terraform destroy
```

## 7. Add button on profile repository

To add a repository button to the profile README at `https://github.com/Shubhankart101/Shubhankart101`, add this Markdown in that repository's `README.md`:

```md
[![FlightPriceMonitorAlertSystem](https://img.shields.io/badge/Repo-FlightPriceMonitorAlertSystem-2ea44f?logo=github)](https://github.com/Shubhankart101/FlightPriceMonitorAlertSystem)
```

If using HTML button style:

```html
<a href="https://github.com/Shubhankart101/FlightPriceMonitorAlertSystem">
  <img src="https://img.shields.io/badge/Open-FlightPriceMonitorAlertSystem-blue?logo=github" alt="FlightPriceMonitorAlertSystem" />
</a>
```
