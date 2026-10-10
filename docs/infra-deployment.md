# Terraform Infrastructure Deployment

## Structure

```text
infra/terraform/
  modules/
    resource_group/
    app_service_plan/
    app_service/
    postgresql/
    redis/
  environments/
    dev/
```

## Modules

- `resource_group`: resource container for all services.
- `app_service_plan`: Linux compute plan.
- `app_service`: deploys containerized Django app and app settings.
- `postgresql`: PostgreSQL flexible server + application database.
- `redis`: managed Redis cache for Celery broker/result backend.

## Environment Composition

The `environments/dev` stack wires all modules together and sets app settings required for Django + Celery runtime:

- Django settings module
- secret key
- DB connection values
- Redis broker/backend values
- container image reference for web app

## Deploy Locally (Developer Flow)

1. Move to environment folder:

```powershell
cd infra/terraform/environments/dev
```

2. Create variables file:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

3. Update secrets in `terraform.tfvars`.

Required values to set:

- `docker_image_name`
- `django_secret_key`
- `db_admin_password`

4. Initialize and validate:

```powershell
terraform init
terraform validate
terraform plan
```

5. Apply:

```powershell
terraform apply
```

## Recommended Plan and Apply Pattern

Use explicit plan output for safer applies:

```powershell
terraform plan -out tfplan
terraform apply tfplan
```

## Destroy (Non-production Cleanup)

```powershell
terraform destroy
```

## Required Cloud Credentials

Use service principal variables in shell or GitHub Secrets:

- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`
- `ARM_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

Use least-privilege service principal access scoped to target subscription/resource group strategy.

## GitHub Actions Integration

- Workflow: `.github/workflows/infra-terraform.yml`
- On PR/push: format, init, validate, plan
- On manual dispatch from main: apply

## Operational Notes

- Keep state backend strategy consistent across environments.
- Never commit real `.tfvars` containing secrets.
- Use `terraform.tfvars.example` as template only.
- Review plan output before apply, especially for destructive changes.

## Outputs

- Web app URL
- PostgreSQL host
- Redis host
- Resource group name

## Troubleshooting

- Auth failure:
  - verify ARM secret values and expiration
- Provider init errors:
  - verify internet/proxy and provider version constraints
- Plan drift unexpectedly large:
  - inspect previous manual changes in Azure Portal
- Apply lock issues (remote backend use-case):
  - confirm no concurrent apply in another pipeline

## Variable Hardening Guidance

- Keep all secret values in secure stores or CI secrets.
- Do not use sample secrets from examples in real environments.
- Rotate database and app secrets on a regular schedule.

## State Management Recommendation

- For team environments, configure remote backend (e.g., Azure storage).
- Enable state locking where backend supports it.
- Keep one state file per environment to avoid accidental cross-env drift.

## Pre-Apply Checklist

1. `terraform fmt -check` passes.
2. `terraform validate` passes.
3. `terraform plan` reviewed by reviewer.
4. Variables and secrets verified for target environment.
5. Rollback plan identified for the change set.

## Post-Apply Verification

- Confirm web app URL output resolves.
- Confirm app settings include required Django and DB/Redis values.
- Confirm DB and Redis resources are reachable from app runtime.
- Run `/api/health/` from deployed endpoint.

## Cost and SKU Considerations

- `B1`/basic SKUs are suitable for dev and light workloads.
- Use production-appropriate SKUs for HA/performance targets.
- Review idle and burst traffic patterns before sizing upgrades.
