# Pipelines

## Workflow Inventory

Workflows live in `.github/workflows/`.

1. `validate.yml`
- Trigger: pull requests and manual.
- Purpose: gate changes with Django + Terraform validation.
- Checks: compileall, `manage.py check`, migration drift, `terraform fmt`, `terraform validate`.

2. `test.yml` (dedicated test pipeline)
- Trigger: push/pull_request/manual.
- Purpose: run unit and API tests in matrix mode.
- Matrix: Python 3.10, 3.11, 3.12.

3. `build-deploy.yml`
- Trigger: push to main and manual.
- Purpose: build Docker image, push to GHCR, deploy to Azure Web App if secrets are configured.
- Required deploy secrets:
  - `AZURE_CREDENTIALS`
  - `AZURE_WEBAPP_NAME`

4. `infra-terraform.yml`
- Trigger: infra path changes and manual.
- Purpose: plan/apply Terraform infrastructure.
- Apply runs only on manual dispatch from `main`.

## Pipeline Stages and Intent

- Validation stage: fast fail for static/runtime config regressions.
- Testing stage: deterministic unit/API quality gates.
- Build stage: reproducible container artifact from `Dockerfile`.
- Deploy stage: environment deployment to Azure App Service.
- Infra stage: Terraform-based cloud provisioning and drift control.

## Branch Strategy Recommendation

- Protect `main`.
- Require `Validation Pipeline` and `Test Pipeline` checks to pass before merge.
- Restrict infra apply to maintainers via workflow permissions.
