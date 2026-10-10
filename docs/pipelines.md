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

## Trigger Matrix

| Workflow | PR | Push main | Manual | Path filtered |
|---|---|---|---|---|
| validate.yml | Yes | No | Yes | No |
| test.yml | Yes | Yes | Yes | No |
| build-deploy.yml | No | Yes | Yes | No |
| infra-terraform.yml | Yes | Yes | Yes | Yes (`infra/terraform/**`) |

## Required Secrets

### Application deploy

- `AZURE_CREDENTIALS`
- `AZURE_WEBAPP_NAME`

### Terraform pipelines

- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`
- `ARM_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## Recommended Repository Protections

- Protect `main` branch.
- Require status checks:
  - Validation Pipeline
  - Test Pipeline
- Require pull request review before merge.
- Restrict who can trigger infrastructure apply.

## Pipeline Stages and Intent

- Validation stage: fast fail for static/runtime config regressions.
- Testing stage: deterministic unit/API quality gates.
- Build stage: reproducible container artifact from `Dockerfile`.
- Deploy stage: environment deployment to Azure App Service.
- Infra stage: Terraform-based cloud provisioning and drift control.

## Build and Deploy Behavior

- Image is built with Buildx and pushed to GHCR.
- Tags include immutable SHA and optional `latest` on default branch.
- Deploy job is conditional on required Azure secrets.

## Terraform Pipeline Behavior

- PR and push runs perform fmt/init/validate/plan.
- Apply is intentionally manual and limited to `main` context.
- This pattern reduces accidental infra changes and supports review-first workflows.

## Failure Triage

1. Validation failures
  - syntax/import/config issue
  - migration drift detected
2. Test failures
  - endpoint behavior change
  - auth scope regression
3. Build failures
  - Docker context or dependency issue
  - registry auth issue
4. Deploy failures
  - Azure credentials invalid/expired
  - app name mismatch
5. Terraform failures
  - provider auth issue
  - missing variable or state conflict

## Branch Strategy Recommendation

- Protect `main`.
- Require `Validation Pipeline` and `Test Pipeline` checks to pass before merge.
- Restrict infra apply to maintainers via workflow permissions.
