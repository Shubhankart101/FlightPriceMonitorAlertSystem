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

## Required Cloud Credentials

Use service principal variables in shell or GitHub Secrets:

- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`
- `ARM_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## Outputs

- Web app URL
- PostgreSQL host
- Redis host
- Resource group name
